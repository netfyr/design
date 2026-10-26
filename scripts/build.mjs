import { createHash } from 'node:crypto';
import { copyFile, cp, lstat, mkdir, readFile, rm, writeFile } from 'node:fs/promises';
import { fileURLToPath } from 'node:url';
import path from 'node:path';
import { artifactFiles, build as buildComponents, output as componentsOutput, regularFile } from '../web/scripts/build.mjs';

const root = fileURLToPath(new URL('../', import.meta.url));
const output = path.join(root, 'dist');
const legacyFont = /^netfyr-(?:(?:mono|sans)-(?:Regular|Semibold)\.(?:otf|ttf|woff2)|fonts-0\.(?:401|506)\.zip)$/;
const publishAsset = source => !legacyFont.test(path.basename(source)) && !/\.pdf$/i.test(source);
for (const directory of ['src', 'public']) {
  const reserved = await lstat(path.join(root, directory, 'components')).catch(error => {
    if (error.code !== 'ENOENT') throw error;
  });
  if (reserved) throw new Error('The components/ output path is reserved for the gallery artifact');
}
await buildComponents();
const previous = await lstat(output).catch(error => {
  if (error.code !== 'ENOENT') throw error;
});
if (previous?.isSymbolicLink()) throw new Error('Refusing to replace a linked output directory');
await rm(output, { recursive: true, force: true });
await mkdir(output, { recursive: true });
await cp(path.join(root, 'public'), output, {
  recursive: true,
  filter: publishAsset,
});
await cp(path.join(root, 'src'), output, { recursive: true, filter: publishAsset });
for (const file of artifactFiles) {
  const destination = path.join(output, 'components', file);
  await mkdir(path.dirname(destination), { recursive: true });
  await copyFile(await regularFile(componentsOutput, file), destination);
}
const indexPath = path.join(output, 'index.html');
let html = await readFile(indexPath, 'utf8');
for (const [file, attribute] of [['styles.css', 'href'], ['app.js', 'src']]) {
  const hash = createHash('sha256').update(await readFile(path.join(output, file))).digest('hex').slice(0, 16);
  const reference = new RegExp(`${attribute}="${file.replace('.', '\\.')}(?:\\?[^"]*)?"`);
  html = html.replace(reference, `${attribute}="${file}?v=${hash}"`);
}
await writeFile(indexPath, html);
console.log('Built netfyr design library in dist/');
