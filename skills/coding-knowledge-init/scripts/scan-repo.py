#!/usr/bin/env python3
"""
scan-repo.py — 扫描单个代码仓库，输出结构化 JSON。

用法:
    python scan-repo.py /path/to/repo --output scan-result.json
    python scan-repo.py /path/to/repo --output-dir /path/to/output/
"""

import argparse
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def run_grep(pattern, path, extra_args=None):
    """Run grep -rn and return list of (file, lineno, line) tuples."""
    cmd = ["grep", "-rn", "--include=*.java", "--include=*.php", "--include=*.go",
           "--include=*.py", "--include=*.ts", "--include=*.js", "--include=*.vue",
           "--include=*.jsx", "--include=*.tsx", "--include=*.kt"]
    if extra_args:
        cmd.extend(extra_args)
    cmd.extend([pattern, str(path)])
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        lines = result.stdout.strip().split("\n") if result.stdout.strip() else []
        out = []
        for line in lines:
            parts = line.split(":", 2)
            if len(parts) >= 3:
                out.append((parts[0], int(parts[1]), parts[2].strip()))
        return out
    except (subprocess.TimeoutExpired, Exception):
        return []


def run_find(path, name_pattern, file_type="f"):
    """Run find and return list of file paths."""
    cmd = ["find", str(path), "-type", file_type, "-name", name_pattern]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        return [p for p in result.stdout.strip().split("\n") if p]
    except (subprocess.TimeoutExpired, Exception):
        return []


def read_file(path, max_lines=500):
    """Read file content, return string. Limit to max_lines."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            lines = []
            for i, line in enumerate(f):
                if i >= max_lines:
                    break
                lines.append(line)
            return "".join(lines)
    except Exception:
        return ""


def dir_tree(path, max_depth=3, prefix=""):
    """Generate directory tree string up to max_depth."""
    entries = []
    try:
        items = sorted(os.listdir(path))
    except PermissionError:
        return entries
    dirs = [i for i in items if os.path.isdir(os.path.join(path, i)) and not i.startswith(".")]
    # Skip common non-source dirs
    skip = {"node_modules", "vendor", "target", "build", "dist", ".git", ".idea",
            "__pycache__", ".gradle", "bin", "out", ".mvn"}
    dirs = [d for d in dirs if d not in skip]
    for d in dirs:
        full = os.path.join(path, d)
        file_count = sum(1 for _ in Path(full).rglob("*") if _.is_file())
        entries.append({"name": d, "path": os.path.relpath(full, path), "file_count": file_count})
        if max_depth > 1:
            sub = dir_tree(full, max_depth - 1, prefix + "  ")
            if sub:
                entries[-1]["children"] = sub
    return entries


def relative(filepath, repo_root):
    """Return relative path from repo root."""
    try:
        return os.path.relpath(filepath, repo_root)
    except ValueError:
        return filepath


# ---------------------------------------------------------------------------
# Tech stack detection
# ---------------------------------------------------------------------------

def detect_tech_stack(repo_path):
    """Detect the tech stack of a repository."""
    stacks = []
    if os.path.exists(os.path.join(repo_path, "pom.xml")) or \
       os.path.exists(os.path.join(repo_path, "build.gradle")) or \
       os.path.exists(os.path.join(repo_path, "build.gradle.kts")):
        stacks.append("java")

    if os.path.exists(os.path.join(repo_path, "go.mod")):
        stacks.append("go")

    if os.path.exists(os.path.join(repo_path, "composer.json")):
        stacks.append("php")

    pkg_json_path = os.path.join(repo_path, "package.json")
    if os.path.exists(pkg_json_path):
        content = read_file(pkg_json_path)
        if any(kw in content for kw in ['"vue"', '"react"', '"@angular"', '"nuxt"', '"next"']):
            stacks.append("frontend")
        if any(kw in content for kw in ['"express"', '"koa"', '"nestjs"', '"@nestjs"', '"fastify"']):
            stacks.append("nodejs")
        if not stacks:
            stacks.append("nodejs")  # default for package.json

    if os.path.exists(os.path.join(repo_path, "requirements.txt")) or \
       os.path.exists(os.path.join(repo_path, "pyproject.toml")) or \
       os.path.exists(os.path.join(repo_path, "setup.py")):
        if "nodejs" not in stacks and "frontend" not in stacks:
            stacks.append("python")

    # Check for PHP directory structure without composer.json
    if "php" not in stacks:
        if os.path.isdir(os.path.join(repo_path, "app", "controllers")) or \
           os.path.isdir(os.path.join(repo_path, "app", "Http", "Controllers")):
            stacks.append("php")

    return stacks if stacks else ["unknown"]


# ---------------------------------------------------------------------------
# Java/Spring scanner
# ---------------------------------------------------------------------------

def parse_pom_xml(pom_path, repo_root):
    """Parse pom.xml for project info and dependencies."""
    info = {"group_id": "", "artifact_id": "", "version": "", "parent": {},
            "modules": [], "dependencies": []}
    try:
        # Strip namespace for easier parsing
        content = read_file(pom_path, max_lines=2000)
        content = re.sub(r'\sxmlns="[^"]+"', '', content, count=1)
        root = ET.fromstring(content)

        info["group_id"] = (root.findtext("groupId") or "").strip()
        info["artifact_id"] = (root.findtext("artifactId") or "").strip()
        info["version"] = (root.findtext("version") or "").strip()

        parent = root.find("parent")
        if parent is not None:
            info["parent"] = {
                "group_id": (parent.findtext("groupId") or "").strip(),
                "artifact_id": (parent.findtext("artifactId") or "").strip(),
                "version": (parent.findtext("version") or "").strip(),
            }

        modules = root.find("modules")
        if modules is not None:
            info["modules"] = [m.text.strip() for m in modules.findall("module") if m.text]

        deps = root.find("dependencies")
        if deps is not None:
            for dep in deps.findall("dependency"):
                g = (dep.findtext("groupId") or "").strip()
                a = (dep.findtext("artifactId") or "").strip()
                v = (dep.findtext("version") or "").strip()
                scope = (dep.findtext("scope") or "").strip()
                if g and a:
                    info["dependencies"].append({
                        "group_id": g, "artifact_id": a, "version": v, "scope": scope
                    })
    except ET.ParseError:
        pass
    return info


def parse_gradle(gradle_path, repo_root):
    """Parse build.gradle for dependencies."""
    info = {"dependencies": [], "plugins": []}
    content = read_file(gradle_path, max_lines=500)
    # Extract dependencies
    dep_pattern = re.compile(
        r"(implementation|api|compile|runtimeOnly|compileOnly|testImplementation)"
        r"""\s+['"]([^'"]+)['"]"""
    )
    for match in dep_pattern.finditer(content):
        info["dependencies"].append({"config": match.group(1), "coordinate": match.group(2)})
    return info


def parse_yaml_config(config_path):
    """Simple key-value extraction from yaml/properties config files."""
    configs = []
    content = read_file(config_path, max_lines=300)
    if not content:
        return configs

    if config_path.endswith(".properties"):
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                key, _, value = line.partition("=")
                configs.append({"key": key.strip(), "value": value.strip(),
                                "file": os.path.basename(config_path)})
    else:
        # YAML: extract key paths (simplified)
        for line in content.split("\n"):
            stripped = line.strip()
            if stripped and not stripped.startswith("#") and ":" in stripped:
                key, _, value = stripped.partition(":")
                value = value.strip()
                if value and not value.startswith("{") and not value.startswith("["):
                    configs.append({"key": key.strip(), "value": value,
                                    "file": os.path.basename(config_path)})
    return configs


def extract_java_method_info(file_path, class_name, repo_root):
    """Extract public methods from a Java file with annotations and Javadoc."""
    content = read_file(file_path, max_lines=2000)
    lines = content.split("\n")
    methods = []

    # Class-level RequestMapping
    class_mapping = ""
    class_mapping_match = re.search(
        r'@RequestMapping\s*\(\s*(?:value\s*=\s*)?["\']([^"\']+)["\']', content
    )
    if class_mapping_match:
        class_mapping = class_mapping_match.group(1)

    i = 0
    while i < len(lines):
        line = lines[i].strip()

        # Detect method-level annotations
        annotations = []
        javadoc = ""

        # Look back for Javadoc and annotations
        if re.match(r'public\s+', line) and "class " not in line and "interface " not in line:
            # Collect annotations above this line
            j = i - 1
            while j >= 0:
                prev = lines[j].strip()
                if prev.startswith("@"):
                    annotations.insert(0, prev)
                    j -= 1
                elif prev == "" or prev.startswith("//"):
                    j -= 1
                elif prev.endswith("*/"):
                    # Find Javadoc start
                    doc_lines = []
                    while j >= 0:
                        doc_line = lines[j].strip()
                        doc_lines.insert(0, doc_line)
                        if doc_line.startswith("/**"):
                            break
                        j -= 1
                    javadoc = " ".join(
                        l.lstrip("/* ").rstrip() for l in doc_lines if l.strip("/* ")
                    )
                    j -= 1
                else:
                    break

            # Extract method signature
            method_line = line
            # Handle multi-line signatures
            paren_count = method_line.count("(") - method_line.count(")")
            k = i + 1
            while paren_count > 0 and k < len(lines):
                method_line += " " + lines[k].strip()
                paren_count += lines[k].count("(") - lines[k].count(")")
                k += 1

            # Parse method signature
            sig_match = re.match(
                r'public\s+(?:static\s+)?(\S+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)',
                method_line
            )
            if sig_match:
                return_type = sig_match.group(1)
                method_name = sig_match.group(2)
                params = sig_match.group(3).strip()

                # Extract HTTP mapping
                http_method = ""
                http_path = ""
                for ann in annotations:
                    mapping_match = re.match(
                        r'@(GetMapping|PostMapping|PutMapping|DeleteMapping|PatchMapping'
                        r'|RequestMapping)\s*\(?\s*(?:value\s*=\s*)?(?:["\']([^"\']*)["\'])?',
                        ann
                    )
                    if mapping_match:
                        ann_type = mapping_match.group(1)
                        path = mapping_match.group(2) or ""
                        method_map = {
                            "GetMapping": "GET", "PostMapping": "POST",
                            "PutMapping": "PUT", "DeleteMapping": "DELETE",
                            "PatchMapping": "PATCH", "RequestMapping": "REQUEST"
                        }
                        http_method = method_map.get(ann_type, "")
                        http_path = (class_mapping.rstrip("/") + "/" + path.lstrip("/")).rstrip("/") if path else class_mapping
                        break

                # Extract method body (first 15 lines)
                body_lines = []
                brace_count = 0
                started = False
                for bl in range(i, min(i + 20, len(lines))):
                    body_lines.append(lines[bl])
                    brace_count += lines[bl].count("{") - lines[bl].count("}")
                    if lines[bl].count("{") > 0:
                        started = True
                    if started and brace_count <= 0:
                        break

                methods.append({
                    "name": method_name,
                    "return_type": return_type,
                    "params": params,
                    "line": i + 1,
                    "annotations": annotations,
                    "http_method": http_method,
                    "http_path": http_path,
                    "javadoc": javadoc[:200] if javadoc else "",
                    "body_preview": "\n".join(body_lines[:15]),
                })
        i += 1

    return {
        "class_name": class_name,
        "file": relative(file_path, repo_root),
        "class_mapping": class_mapping,
        "methods": methods,
    }


def scan_java(repo_path):
    """Scan a Java/Spring repository."""
    result = {
        "build": {},
        "modules": [],
        "directory_tree": [],
        "configs": [],
        "controllers": [],
        "services": [],
        "repositories": [],
        "entities": [],
        "cross_service_calls": [],
        "mq": [],
        "scheduled_tasks": [],
        "sql_files": [],
        "enums": [],
    }

    # 1. Build file
    pom_path = os.path.join(repo_path, "pom.xml")
    gradle_path = os.path.join(repo_path, "build.gradle")
    if os.path.exists(pom_path):
        result["build"] = parse_pom_xml(pom_path, repo_path)
        # Also parse sub-module pom.xml files
        for mod in result["build"].get("modules", []):
            sub_pom = os.path.join(repo_path, mod, "pom.xml")
            if os.path.exists(sub_pom):
                sub_info = parse_pom_xml(sub_pom, repo_path)
                result["modules"].append({"name": mod, "build_info": sub_info})
    elif os.path.exists(gradle_path):
        result["build"] = parse_gradle(gradle_path, repo_path)

    # 2. Directory tree
    result["directory_tree"] = dir_tree(repo_path, max_depth=3)

    # 3. Config files
    config_patterns = ["application.properties", "application.yml", "application.yaml",
                       "application-*.yml", "application-*.yaml", "application-*.properties",
                       "bootstrap.yml", "bootstrap.yaml"]
    for pattern in config_patterns:
        for f in run_find(repo_path, pattern):
            result["configs"].extend(parse_yaml_config(f))

    # 4. Controllers
    controller_hits = run_grep("@Controller\\|@RestController", repo_path)
    seen_files = set()
    for filepath, lineno, line in controller_hits:
        if filepath in seen_files or not filepath.endswith(".java"):
            continue
        seen_files.add(filepath)
        class_match = re.search(r'class\s+(\w+)', read_file(filepath, 50))
        class_name = class_match.group(1) if class_match else os.path.basename(filepath).replace(".java", "")
        info = extract_java_method_info(filepath, class_name, repo_path)
        if info:
            result["controllers"].append(info)

    # 5. Services
    service_hits = run_grep("@Service", repo_path)
    seen_files = set()
    for filepath, lineno, line in service_hits:
        if filepath in seen_files or not filepath.endswith(".java"):
            continue
        seen_files.add(filepath)
        class_match = re.search(r'class\s+(\w+)', read_file(filepath, 50))
        class_name = class_match.group(1) if class_match else os.path.basename(filepath).replace(".java", "")
        info = extract_java_method_info(filepath, class_name, repo_path)
        if info:
            result["services"].append(info)

    # 6. Repositories / Mappers
    repo_hits = run_grep("@Repository\\|@Mapper", repo_path)
    seen_files = set()
    for filepath, lineno, line in repo_hits:
        if filepath in seen_files or not filepath.endswith(".java"):
            continue
        seen_files.add(filepath)
        class_match = re.search(r'(?:class|interface)\s+(\w+)', read_file(filepath, 50))
        class_name = class_match.group(1) if class_match else os.path.basename(filepath).replace(".java", "")
        info = extract_java_method_info(filepath, class_name, repo_path)
        if info:
            result["repositories"].append(info)

    # 7. Entities / DOs
    entity_hits = run_grep("@Entity\\|@Table", repo_path)
    entity_files = run_find(repo_path, "*Entity.java") + run_find(repo_path, "*DO.java")
    seen_files = set()
    all_entity_files = set(f for f, _, _ in entity_hits) | set(entity_files)
    for filepath in all_entity_files:
        if filepath in seen_files or not filepath.endswith(".java"):
            continue
        seen_files.add(filepath)
        content = read_file(filepath, 300)
        class_match = re.search(r'class\s+(\w+)', content)
        class_name = class_match.group(1) if class_match else os.path.basename(filepath).replace(".java", "")

        # Extract table name
        table_match = re.search(r'@Table\s*\(\s*name\s*=\s*["\']([^"\']+)["\']', content)
        table_name = table_match.group(1) if table_match else ""

        # Extract fields
        fields = []
        for field_match in re.finditer(
            r'private\s+(\S+(?:<[^>]+>)?)\s+(\w+)\s*;', content
        ):
            field_type = field_match.group(1)
            field_name = field_match.group(2)
            # Look for @Column annotation above
            fields.append({"name": field_name, "type": field_type})

        result["entities"].append({
            "class_name": class_name,
            "file": relative(filepath, repo_path),
            "table_name": table_name,
            "fields": fields,
        })

    # 8. Cross-service calls
    cross_patterns = [
        ("@FeignClient", r'@FeignClient\s*\([^)]*(?:name|value)\s*=\s*["\']([^"\']+)["\']'),
        ("@AmsMeshClient", r'@AmsMeshClient\s*\([^)]*appId\s*=\s*["\']([^"\']+)["\']'),
        ("XMeshClient", r'XMeshClient\s*\([^)]*["\']([^"\']+)["\']'),
        ("RestTemplate", None),
    ]
    for annotation, pattern in cross_patterns:
        hits = run_grep(annotation, repo_path)
        for filepath, lineno, line in hits:
            target = ""
            if pattern:
                m = re.search(pattern, line)
                if m:
                    target = m.group(1)
            # Extract interface methods from the file
            content = read_file(filepath, 500)
            interface_methods = []
            for mm in re.finditer(r'(?:@(?:Get|Post|Put|Delete)Mapping\s*\([^)]*\)\s+)?'
                                  r'(\S+(?:<[^>]+>)?)\s+(\w+)\s*\(([^)]*)\)', content):
                interface_methods.append({
                    "return_type": mm.group(1),
                    "name": mm.group(2),
                    "params": mm.group(3).strip(),
                })

            result["cross_service_calls"].append({
                "type": annotation,
                "target_app_id": target,
                "file": relative(filepath, repo_path),
                "line": lineno,
                "methods": interface_methods[:20],  # limit
            })

    # 9. MQ
    mq_patterns = ["@KafkaListener", "@RabbitListener", "PulsarConsumer",
                    "CMQConsumer", "PulsarProducer", "KafkaTemplate",
                    "RabbitTemplate", "CMQProducer"]
    for pat in mq_patterns:
        hits = run_grep(pat, repo_path)
        for filepath, lineno, line in hits:
            topic_match = re.search(r'topic[s]?\s*=\s*["\']([^"\']+)["\']', line)
            queue_match = re.search(r'queue[s]?\s*=\s*["\']([^"\']+)["\']', line)
            topic = (topic_match or queue_match)
            direction = "consume" if "Listener" in pat or "Consumer" in pat else "produce"
            result["mq"].append({
                "type": pat,
                "topic": topic.group(1) if topic else "",
                "direction": direction,
                "file": relative(filepath, repo_path),
                "line": lineno,
                "context": line[:200],
            })

    # 10. Scheduled tasks
    sched_hits = run_grep("@Scheduled\\|@SaturnJob\\|@XxlJob", repo_path)
    for filepath, lineno, line in sched_hits:
        cron_match = re.search(r'cron\s*=\s*["\']([^"\']+)["\']', line)
        result["scheduled_tasks"].append({
            "file": relative(filepath, repo_path),
            "line": lineno,
            "cron": cron_match.group(1) if cron_match else "",
            "context": line[:200],
        })

    # 11. SQL files
    sql_files = run_find(repo_path, "*.sql")
    migration_dirs = []
    for d in ["db", "migration", "migrations", "sql", "schema", "flyway", "liquibase"]:
        candidate = os.path.join(repo_path, d)
        if os.path.isdir(candidate):
            migration_dirs.append(relative(candidate, repo_path))
        # Also check in sub-modules
        for mod in result["build"].get("modules", []):
            candidate = os.path.join(repo_path, mod, "src", "main", "resources", d)
            if os.path.isdir(candidate):
                migration_dirs.append(relative(candidate, repo_path))

    for sf in sql_files:
        content = read_file(sf, 200)
        result["sql_files"].append({
            "file": relative(sf, repo_path),
            "preview": content[:2000],
        })
    if migration_dirs:
        result["migration_dirs"] = migration_dirs

    # 12. Enums
    enum_files = run_find(repo_path, "*Enum.java")
    for ef in enum_files:
        content = read_file(ef, 200)
        class_match = re.search(r'enum\s+(\w+)', content)
        enum_name = class_match.group(1) if class_match else os.path.basename(ef).replace(".java", "")
        # Extract enum values
        values = []
        enum_body_match = re.search(r'enum\s+\w+[^{]*\{([^;]+);', content, re.DOTALL)
        if enum_body_match:
            body = enum_body_match.group(1)
            for val_match in re.finditer(r'(\w+)\s*(?:\([^)]*\))?', body):
                val = val_match.group(1)
                if val not in ("", "public", "private", "protected", "static", "final"):
                    values.append(val)
        result["enums"].append({
            "class_name": enum_name,
            "file": relative(ef, repo_path),
            "values": values[:50],  # limit
        })

    return result


# ---------------------------------------------------------------------------
# PHP scanner
# ---------------------------------------------------------------------------

def scan_php(repo_path):
    """Scan a PHP repository."""
    result = {
        "composer": {},
        "directory_tree": [],
        "routes": [],
        "controllers": [],
        "models": [],
        "configs": [],
        "migrations": [],
    }

    # 1. composer.json
    composer_path = os.path.join(repo_path, "composer.json")
    if os.path.exists(composer_path):
        try:
            result["composer"] = json.loads(read_file(composer_path))
        except json.JSONDecodeError:
            pass

    # 2. Directory tree
    result["directory_tree"] = dir_tree(repo_path, max_depth=3)

    # 3. Routes
    route_dirs = ["routes", "config"]
    for rd in route_dirs:
        route_path = os.path.join(repo_path, rd)
        if os.path.isdir(route_path):
            for rf in run_find(route_path, "*.php"):
                content = read_file(rf, 300)
                result["routes"].append({
                    "file": relative(rf, repo_path),
                    "content": content[:3000],
                })

    # Also check routes.php directly
    for rfile in ["config/routes.php", "routes/web.php", "routes/api.php"]:
        full = os.path.join(repo_path, rfile)
        if os.path.exists(full):
            content = read_file(full, 300)
            result["routes"].append({
                "file": rfile,
                "content": content[:3000],
            })

    # 4. Controllers
    controller_dirs = [
        os.path.join(repo_path, "app", "controllers"),
        os.path.join(repo_path, "app", "Http", "Controllers"),
        os.path.join(repo_path, "controllers"),
    ]
    for cd in controller_dirs:
        if os.path.isdir(cd):
            for cf in run_find(cd, "*.php"):
                content = read_file(cf, 500)
                class_match = re.search(r'class\s+(\w+)', content)
                class_name = class_match.group(1) if class_match else os.path.basename(cf).replace(".php", "")
                methods = []
                for mm in re.finditer(
                    r'public\s+function\s+(\w+)\s*\(([^)]*)\)', content
                ):
                    methods.append({
                        "name": mm.group(1),
                        "params": mm.group(2).strip(),
                    })
                result["controllers"].append({
                    "class_name": class_name,
                    "file": relative(cf, repo_path),
                    "methods": methods,
                })

    # 5. Models
    model_dirs = [
        os.path.join(repo_path, "app", "models"),
        os.path.join(repo_path, "app", "Models"),
        os.path.join(repo_path, "models"),
    ]
    for md in model_dirs:
        if os.path.isdir(md):
            for mf in run_find(md, "*.php"):
                content = read_file(mf, 300)
                class_match = re.search(r'class\s+(\w+)', content)
                class_name = class_match.group(1) if class_match else os.path.basename(mf).replace(".php", "")

                # Extract table name
                table_match = re.search(r'\$table\s*=\s*["\']([^"\']+)["\']', content)
                table_name = table_match.group(1) if table_match else ""

                result["models"].append({
                    "class_name": class_name,
                    "file": relative(mf, repo_path),
                    "table_name": table_name,
                })

    # 6. Config files
    config_dirs = ["conf", "config", ".env"]
    for cd in config_dirs:
        full = os.path.join(repo_path, cd)
        if os.path.isfile(full):
            content = read_file(full, 200)
            for line in content.split("\n"):
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    key, _, value = line.partition("=")
                    result["configs"].append({"key": key.strip(), "value": value.strip(), "file": cd})
        elif os.path.isdir(full):
            for cf in run_find(full, "*.php") + run_find(full, "*.ini") + run_find(full, "*.yaml"):
                content = read_file(cf, 100)
                result["configs"].append({
                    "file": relative(cf, repo_path),
                    "preview": content[:1000],
                })

    # 7. Migrations
    migration_dirs = ["database/migrations", "migrations", "db/migrations"]
    for md in migration_dirs:
        full = os.path.join(repo_path, md)
        if os.path.isdir(full):
            for mf in sorted(run_find(full, "*.php") + run_find(full, "*.sql")):
                content = read_file(mf, 200)
                result["migrations"].append({
                    "file": relative(mf, repo_path),
                    "preview": content[:2000],
                })

    return result


# ---------------------------------------------------------------------------
# Go scanner
# ---------------------------------------------------------------------------

def scan_go(repo_path):
    """Scan a Go repository."""
    result = {
        "go_mod": {},
        "directory_tree": [],
        "handlers": [],
        "structs": [],
        "sql_files": [],
        "grpc_services": [],
    }

    # 1. go.mod
    gomod_path = os.path.join(repo_path, "go.mod")
    if os.path.exists(gomod_path):
        content = read_file(gomod_path, 200)
        module_match = re.search(r'module\s+(\S+)', content)
        result["go_mod"]["module"] = module_match.group(1) if module_match else ""
        deps = []
        for dep_match in re.finditer(r'^\s+(\S+)\s+(v\S+)', content, re.MULTILINE):
            deps.append({"path": dep_match.group(1), "version": dep_match.group(2)})
        result["go_mod"]["dependencies"] = deps

    # 2. Directory tree
    result["directory_tree"] = dir_tree(repo_path, max_depth=3)

    # 3. HTTP handlers
    handler_patterns = [
        r'\.GET\s*\(',
        r'\.POST\s*\(',
        r'\.PUT\s*\(',
        r'\.DELETE\s*\(',
        r'\.Handle\s*\(',
        r'\.HandleFunc\s*\(',
        r'http\.HandleFunc\s*\(',
    ]
    for pat in handler_patterns:
        hits = run_grep(pat, repo_path)
        for filepath, lineno, line in hits:
            if not filepath.endswith(".go"):
                continue
            path_match = re.search(r'["\']([^"\']+)["\']', line)
            result["handlers"].append({
                "file": relative(filepath, repo_path),
                "line": lineno,
                "path": path_match.group(1) if path_match else "",
                "context": line[:200],
            })

    # 4. Struct definitions
    struct_hits = run_grep(r'type\s\+\w\+\s\+struct', repo_path)
    for filepath, lineno, line in struct_hits:
        if not filepath.endswith(".go"):
            continue
        struct_match = re.search(r'type\s+(\w+)\s+struct', line)
        if struct_match:
            struct_name = struct_match.group(1)
            # Read fields
            content = read_file(filepath, 500)
            result["structs"].append({
                "name": struct_name,
                "file": relative(filepath, repo_path),
                "line": lineno,
            })

    # 5. SQL files
    sql_files = run_find(repo_path, "*.sql")
    for sf in sql_files:
        content = read_file(sf, 200)
        result["sql_files"].append({
            "file": relative(sf, repo_path),
            "preview": content[:2000],
        })

    # 6. gRPC services
    proto_files = run_find(repo_path, "*.proto")
    for pf in proto_files:
        content = read_file(pf, 300)
        services = re.findall(r'service\s+(\w+)\s*\{', content)
        rpcs = re.findall(r'rpc\s+(\w+)\s*\((\w+)\)\s*returns\s*\((\w+)\)', content)
        result["grpc_services"].append({
            "file": relative(pf, repo_path),
            "services": services,
            "rpcs": [{"name": r[0], "request": r[1], "response": r[2]} for r in rpcs],
        })

    return result


# ---------------------------------------------------------------------------
# Frontend scanner
# ---------------------------------------------------------------------------

def scan_frontend(repo_path):
    """Scan a frontend (Vue/React) repository."""
    result = {
        "package_json": {},
        "directory_tree": [],
        "routes": [],
        "api_calls": [],
        "stores": [],
        "pages": [],
    }

    # 1. package.json
    pkg_path = os.path.join(repo_path, "package.json")
    if os.path.exists(pkg_path):
        try:
            result["package_json"] = json.loads(read_file(pkg_path))
        except json.JSONDecodeError:
            pass

    # 2. Directory tree
    result["directory_tree"] = dir_tree(repo_path, max_depth=3)

    # 3. Router config
    router_files = run_find(repo_path, "router.*")
    for rf in router_files:
        if any(rf.endswith(ext) for ext in [".js", ".ts", ".jsx", ".tsx"]):
            content = read_file(rf, 300)
            result["routes"].append({
                "file": relative(rf, repo_path),
                "content": content[:3000],
            })

    # 4. API layer
    api_dirs = ["api", "services", "service"]
    for ad in api_dirs:
        for sub in ["src", "."]:
            full = os.path.join(repo_path, sub, ad)
            if os.path.isdir(full):
                for af in run_find(full, "*.ts") + run_find(full, "*.js"):
                    content = read_file(af, 200)
                    result["api_calls"].append({
                        "file": relative(af, repo_path),
                        "content": content[:2000],
                    })

    # 5. State management
    store_dirs = ["store", "stores", "pinia", "redux", "vuex"]
    for sd in store_dirs:
        for sub in ["src", "."]:
            full = os.path.join(repo_path, sub, sd)
            if os.path.isdir(full):
                for sf in run_find(full, "*.ts") + run_find(full, "*.js"):
                    content = read_file(sf, 200)
                    result["stores"].append({
                        "file": relative(sf, repo_path),
                        "content": content[:2000],
                    })

    # 6. Pages / Views
    page_dirs = ["pages", "views"]
    for pd in page_dirs:
        for sub in ["src", "."]:
            full = os.path.join(repo_path, sub, pd)
            if os.path.isdir(full):
                for pf in (run_find(full, "*.vue") + run_find(full, "*.tsx")
                           + run_find(full, "*.jsx")):
                    result["pages"].append({
                        "file": relative(pf, repo_path),
                        "name": os.path.basename(pf),
                    })

    return result


# ---------------------------------------------------------------------------
# Node.js scanner
# ---------------------------------------------------------------------------

def scan_nodejs(repo_path):
    """Scan a Node.js backend repository."""
    result = {
        "package_json": {},
        "directory_tree": [],
        "routes": [],
        "controllers": [],
        "models": [],
        "configs": [],
    }

    # 1. package.json
    pkg_path = os.path.join(repo_path, "package.json")
    if os.path.exists(pkg_path):
        try:
            result["package_json"] = json.loads(read_file(pkg_path))
        except json.JSONDecodeError:
            pass

    # 2. Directory tree
    result["directory_tree"] = dir_tree(repo_path, max_depth=3)

    # 3. Routes
    route_patterns = ["routes", "router"]
    for rp in route_patterns:
        for sub in ["src", ".", "app"]:
            full = os.path.join(repo_path, sub, rp)
            if os.path.isdir(full):
                for rf in run_find(full, "*.ts") + run_find(full, "*.js"):
                    content = read_file(rf, 300)
                    result["routes"].append({
                        "file": relative(rf, repo_path),
                        "content": content[:3000],
                    })

    # 4. Controllers
    controller_dirs = ["controllers", "controller"]
    for cd in controller_dirs:
        for sub in ["src", ".", "app"]:
            full = os.path.join(repo_path, sub, cd)
            if os.path.isdir(full):
                for cf in run_find(full, "*.ts") + run_find(full, "*.js"):
                    content = read_file(cf, 500)
                    result["controllers"].append({
                        "file": relative(cf, repo_path),
                        "content": content[:3000],
                    })

    # NestJS controllers
    nest_hits = run_grep("@Controller", repo_path)
    seen = set()
    for filepath, lineno, line in nest_hits:
        if filepath in seen:
            continue
        seen.add(filepath)
        content = read_file(filepath, 500)
        result["controllers"].append({
            "file": relative(filepath, repo_path),
            "content": content[:3000],
        })

    # 5. Models
    model_dirs = ["models", "model", "entities", "entity"]
    for md in model_dirs:
        for sub in ["src", ".", "app"]:
            full = os.path.join(repo_path, sub, md)
            if os.path.isdir(full):
                for mf in run_find(full, "*.ts") + run_find(full, "*.js"):
                    content = read_file(mf, 300)
                    result["models"].append({
                        "file": relative(mf, repo_path),
                        "content": content[:2000],
                    })

    return result


# ---------------------------------------------------------------------------
# Python scanner
# ---------------------------------------------------------------------------

def scan_python(repo_path):
    """Scan a Python repository."""
    result = {
        "requirements": [],
        "directory_tree": [],
        "routes": [],
        "models": [],
        "configs": [],
    }

    # 1. Dependencies
    req_path = os.path.join(repo_path, "requirements.txt")
    if os.path.exists(req_path):
        content = read_file(req_path, 200)
        for line in content.split("\n"):
            line = line.strip()
            if line and not line.startswith("#"):
                result["requirements"].append(line)

    pyproject_path = os.path.join(repo_path, "pyproject.toml")
    if os.path.exists(pyproject_path):
        content = read_file(pyproject_path, 300)
        result["pyproject"] = content[:3000]

    # 2. Directory tree
    result["directory_tree"] = dir_tree(repo_path, max_depth=3)

    # 3. Routes (Flask/FastAPI/Django)
    route_hits = run_grep(r"@app\.\(get\|post\|put\|delete\|route\)\|@router\.\|urlpatterns", repo_path)
    for filepath, lineno, line in route_hits:
        result["routes"].append({
            "file": relative(filepath, repo_path),
            "line": lineno,
            "context": line[:200],
        })

    # 4. Models
    model_hits = run_grep(r"class.*Model\)\|class.*db\.Model\|class.*Base\)", repo_path)
    for filepath, lineno, line in model_hits:
        result["models"].append({
            "file": relative(filepath, repo_path),
            "line": lineno,
            "context": line[:200],
        })

    return result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def scan_repo(repo_path):
    """Main scan function — detect tech stack and run appropriate scanners."""
    repo_path = os.path.abspath(repo_path)
    repo_name = os.path.basename(repo_path)

    if not os.path.isdir(repo_path):
        print(f"Error: {repo_path} is not a directory", file=sys.stderr)
        sys.exit(1)

    stacks = detect_tech_stack(repo_path)

    result = {
        "repo_name": repo_name,
        "repo_path": repo_path,
        "tech_stacks": stacks,
        "scans": {},
    }

    scanner_map = {
        "java": scan_java,
        "php": scan_php,
        "go": scan_go,
        "frontend": scan_frontend,
        "nodejs": scan_nodejs,
        "python": scan_python,
    }

    for stack in stacks:
        if stack in scanner_map:
            print(f"  Scanning {repo_name} as {stack}...", file=sys.stderr)
            result["scans"][stack] = scanner_map[stack](repo_path)
        else:
            print(f"  Unknown stack '{stack}' for {repo_name}, skipping.", file=sys.stderr)
            result["scans"][stack] = {"directory_tree": dir_tree(repo_path, max_depth=3)}

    return result


def main():
    parser = argparse.ArgumentParser(description="Scan a code repository and output structured JSON.")
    parser.add_argument("repo_path", help="Path to the repository to scan")
    parser.add_argument("--output", "-o", help="Output JSON file path")
    parser.add_argument("--output-dir", "-d", help="Output directory (file will be named {repo-name}.scan-result.json)")
    args = parser.parse_args()

    result = scan_repo(args.repo_path)

    if args.output_dir:
        os.makedirs(args.output_dir, exist_ok=True)
        output_path = os.path.join(args.output_dir, f"{result['repo_name']}.scan-result.json")
    elif args.output:
        output_path = args.output
    else:
        output_path = None

    json_str = json.dumps(result, ensure_ascii=False, indent=2, default=str)

    if output_path:
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(json_str)
        print(f"Scan complete. Output written to: {output_path}", file=sys.stderr)
    else:
        print(json_str)


if __name__ == "__main__":
    main()
