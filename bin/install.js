#!/usr/bin/env node

const fs = require('fs');
const path = require('path');

const HOME = process.env.HOME || process.env.USERPROFILE;
const SKILLS_TARGET = path.join(HOME, '.claude', 'skills');
const skillsSource = path.join(__dirname, '..', 'skills');

// Uninstall mode
if (process.argv.includes('--uninstall')) {
  const skills = fs.readdirSync(skillsSource).filter((name) => {
    return fs.statSync(path.join(skillsSource, name)).isDirectory();
  });

  let count = 0;
  for (const skill of skills) {
    const dest = path.join(SKILLS_TARGET, skill);
    if (fs.existsSync(dest)) {
      fs.rmSync(dest, { recursive: true, force: true });
      console.log(`  Removing: ${skill}`);
      count++;
    }
  }

  console.log('');
  console.log(count === 0 ? 'No skills found to remove.' : `Done! Removed ${count} skills from ${SKILLS_TARGET}`);
  process.exit(0);
}

// Install mode
if (!fs.existsSync(skillsSource)) {
  console.error('Error: skills/ directory not found.');
  process.exit(1);
}

fs.mkdirSync(SKILLS_TARGET, { recursive: true });

const skills = fs.readdirSync(skillsSource).filter((name) => {
  return fs.statSync(path.join(skillsSource, name)).isDirectory();
});

let count = 0;
for (const skill of skills) {
  const src = path.join(skillsSource, skill);
  const dest = path.join(SKILLS_TARGET, skill);

  if (fs.existsSync(dest)) {
    fs.rmSync(dest, { recursive: true, force: true });
  }

  copyDirSync(src, dest);
  console.log(`  Installing: ${skill}`);
  count++;
}

console.log('');
console.log(`Done! Installed ${count} skills to ${SKILLS_TARGET}`);
console.log('Use /skill-name in Claude Code to invoke them.');

function copyDirSync(src, dest) {
  fs.mkdirSync(dest, { recursive: true });
  for (const entry of fs.readdirSync(src, { withFileTypes: true })) {
    const srcPath = path.join(src, entry.name);
    const destPath = path.join(dest, entry.name);
    if (entry.isDirectory()) {
      copyDirSync(srcPath, destPath);
    } else {
      fs.copyFileSync(srcPath, destPath);
    }
  }
}
