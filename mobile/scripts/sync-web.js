/**
 * Copy tablet-app/ into mobile/www for Capacitor packaging.
 * Disables service worker registration in the packaged APK (WebView loads local files).
 */
const fs = require("fs");
const path = require("path");

const root = path.resolve(__dirname, "..", "..");
const src = path.join(root, "tablet-app");
const dest = path.join(__dirname, "..", "www");

function rimraf(dir) {
  if (!fs.existsSync(dir)) return;
  fs.rmSync(dir, { recursive: true, force: true });
}

function copyDir(from, to) {
  fs.mkdirSync(to, { recursive: true });
  for (const entry of fs.readdirSync(from, { withFileTypes: true })) {
    if (entry.name === "README.md") continue;
    const s = path.join(from, entry.name);
    const d = path.join(to, entry.name);
    if (entry.isDirectory()) copyDir(s, d);
    else fs.copyFileSync(s, d);
  }
}

if (!fs.existsSync(path.join(src, "index.html"))) {
  console.error("tablet-app/index.html missing");
  process.exit(1);
}

rimraf(dest);
copyDir(src, dest);

// Capacitor serves from https://localhost — SW can confuse WebView; strip registration.
const appJs = path.join(dest, "js", "app.js");
if (fs.existsSync(appJs)) {
  let text = fs.readFileSync(appJs, "utf8");
  text = text.replace(
    /\/\/ Service worker only helps[\s\S]*?catch\s*\{[\s\S]*?\}\s*\}/,
    "/* service worker disabled in Capacitor APK */"
  );
  fs.writeFileSync(appJs, text);
}

// Mark packaged build so UI can hide web-only install prompts.
const indexPath = path.join(dest, "index.html");
let html = fs.readFileSync(indexPath, "utf8");
if (!html.includes("data-packaged=")) {
  html = html.replace("<html lang=\"en\">", '<html lang="en" data-packaged="capacitor">');
}
fs.writeFileSync(indexPath, html);

console.log("Synced tablet-app -> mobile/www");
