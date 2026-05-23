// Mocks browser APIs that require real hardware so Playwright can drive the app
// without a physical camera, GPS, or motion sensors.
//
// Real test frames are served from http://localhost:8082/ (run test/serve.py).
// The mock cycles through them so the sharpness scorer captures real images.

// --- getUserMedia → canvas cycling through real test frames ---
const origGetUserMedia = navigator.mediaDevices?.getUserMedia?.bind(navigator.mediaDevices);
if (navigator.mediaDevices) {
  navigator.mediaDevices.getUserMedia = async (constraints) => {
    if (!constraints || !constraints.video) {
      return origGetUserMedia(constraints);
    }

    const FRAME_COUNT = 5;
    const FRAME_MS    = 3000;  // hold each frame long enough for the 2000ms cooldown to pass

    const canvas = document.createElement('canvas');
    canvas.width  = 1280;
    canvas.height = 720;
    const ctx = canvas.getContext('2d');

    ctx.fillStyle = '#1a1a1a';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Preload all test frames from the local test data server
    const images = await Promise.all(
      Array.from({ length: FRAME_COUNT }, (_, i) => new Promise(resolve => {
        const img = new Image();
        img.crossOrigin = 'anonymous';
        img.onload  = () => resolve(img);
        img.onerror = () => resolve(null);
        img.src = `http://localhost:8082/data/${i + 1}.jpg`;
      }))
    );

    let idx = 0;
    function drawNext() {
      const img = images[idx % images.length];
      if (img) {
        ctx.drawImage(img, 0, 0, canvas.width, canvas.height);
      } else {
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = '#ff6600';
        ctx.font = '24px sans-serif';
        ctx.fillText(`Frame ${idx + 1} (load failed)`, 40, canvas.height / 2);
      }
      idx = (idx + 1) % FRAME_COUNT;
    }

    drawNext();
    setInterval(drawNext, FRAME_MS);

    return canvas.captureStream(10);
  };
}

// --- DeviceMotionEvent.requestPermission → auto-grant ---
if (typeof DeviceMotionEvent !== 'undefined') {
  DeviceMotionEvent.requestPermission = async () => 'granted';
}

// --- Geolocation → fixed coordinates (Denver, CO) ---
const mockPosition = {
  coords: {
    latitude: 39.7392,
    longitude: -104.9903,
    accuracy: 10,
    altitude: null,
    altitudeAccuracy: null,
    heading: null,
    speed: null,
  },
  timestamp: Date.now(),
};
navigator.geolocation.getCurrentPosition = (success) => success(mockPosition);
navigator.geolocation.watchPosition = (success) => { success(mockPosition); return 1; };
