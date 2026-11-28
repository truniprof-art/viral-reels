Remotion + Three.js template (React → MP4). Remotion License: FREE for individuals and for-profit orgs with ≤3 employees
(company licence needed above that). Render with the pre-installed Chromium:
  cd studio/remotion && npm i && npx remotion render src/index.ts Scene3D out.mp4 \
     --browser-executable=/opt/pw-browsers/chromium-1243/chrome-linux64/chrome --gl=swangle --props='{"title":"HELLO"}'
Measured here (2 CPU, no GPU): a 3 s 1080x1920 clip (90 frames, Three.js scene) rendered in ~31 s incl. bundling. node_modules is not committed.
