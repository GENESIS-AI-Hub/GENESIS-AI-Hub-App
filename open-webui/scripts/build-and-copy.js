import { execSync } from 'child_process';
import fs from 'fs';
import path from 'path';
import { fileURLToPath } from 'url';

const __filename = fileURLToPath(import.meta.url);
const __dirname = path.dirname(__filename);

const rootDir = path.resolve(__dirname, '..');
const buildDir = path.join(rootDir, 'build');
const backendStaticDir = path.join(rootDir, 'backend', 'static');

console.log('Building frontend...');
try {
    execSync('npm run build', { stdio: 'inherit', cwd: rootDir });
} catch (error) {
    console.error('Build failed:', error);
    process.exit(1);
}

console.log(`Copying build artifacts to ${backendStaticDir}...`);

if (fs.existsSync(backendStaticDir)) {
    console.log('Cleaning backend/static...');
    fs.rmSync(backendStaticDir, { recursive: true, force: true });
}

// Helper to copy directory recursively
function copyDir(src, dest) {
    if (!fs.existsSync(dest)) {
        fs.mkdirSync(dest, { recursive: true });
    }
    const entries = fs.readdirSync(src, { withFileTypes: true });

    for (const entry of entries) {
        const srcPath = path.join(src, entry.name);
        const destPath = path.join(dest, entry.name);

        if (entry.isDirectory()) {
            copyDir(srcPath, destPath);
        } else {
            fs.copyFileSync(srcPath, destPath);
        }
    }
}

copyDir(buildDir, backendStaticDir);

console.log('Done! Frontend built and copied to backend/static.');
