---
name: project-client-frame-pipeline
description: Client-side frame filtering design — sharpness scoring, adaptive threshold, cooldown, JPEG encode
metadata:
  type: project
---

The audit app client filters video frames before uploading to reduce server load. Key design decisions:

- Score sharpness using **variance of the Laplacian** on a downsampled grayscale copy of the frame
- **Full-res frame** is captured separately from the scoring canvas for transmission
- Adaptive threshold: **75th percentile of a rolling window** (~60 frames / ~2s) of recent scores — self-calibrates across lighting conditions; avoids fixed thresholds that break in dim environments
- **Cooldown gate** (e.g. 2s) between sends prevents burst-sending when a scene suddenly sharpens
- Frames transmitted as **JPEG via canvas.toBlob()** to minimize payload size

**Why:** Let the phone do cheap filtering so the server only receives clean, unique frames. Downsampling keeps CPU/battery impact low on mobile.

**How to apply:** When touching frame capture or upload logic, preserve all four gate conditions (sharpness score, adaptive threshold, cooldown, JPEG encode). Related: [[project-audit-app]]
