# Excalidraw identity

The banner and logo use Excalidraw 0.18.1, its rough strokes and Virgil handwriting
font. Open `docs/assets/banner.excalidraw` or `icon.excalidraw` in Excalidraw to
edit the scenes. SVG and PNG exports are bundled; no build is needed to view them.
The diagram and its numbers are schematic, not extraction evidence.

For a reproducible design export with Node.js 22.12+:

```bash
cd design
npm install
npm run dev
```

Open the printed localhost URL. `brand.js` constructs the scenes and uses
Excalidraw's native `exportToSvg`, `exportToBlob` and `serializeAsJSON`. The local
Vite middleware writes the six named assets into `docs/assets`. It accepts only
those filenames. Stop the server when finished. The gallery build deliberately
does not overwrite these designs or the three editorial READMEs.

Excalidraw is MIT-licensed. Virgil, by Ellinor Rapp, uses SIL OFL 1.1; see
[VIRGIL-LICENSE](VIRGIL-LICENSE),
[Excalidraw](https://github.com/excalidraw/excalidraw) and its copyright notices.
