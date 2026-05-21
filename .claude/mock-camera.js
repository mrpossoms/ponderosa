// Mocks browser APIs that require real hardware so Playwright can drive the app
// without a physical camera, GPS, or motion sensors.

// --- getUserMedia → silent black video track ---
const origGetUserMedia = navigator.mediaDevices?.getUserMedia?.bind(navigator.mediaDevices);
if (navigator.mediaDevices) {
  navigator.mediaDevices.getUserMedia = async (constraints) => {
    if (constraints && constraints.video) {
      const canvas = document.createElement('canvas');
      canvas.width = 320; canvas.height = 240;
      const ctx = canvas.getContext('2d');
      // Draw a dark frame so sharpness scorer gets real pixels
      ctx.fillStyle = '#1a1a1a';
      ctx.fillRect(0, 0, 320, 240);
      ctx.fillStyle = '#ff6600';
      ctx.font = '20px sans-serif';
      ctx.fillText('MOCK CAMERA', 60, 120);
      setInterval(() => {
        ctx.clearRect(0, 0, 320, 240);
        ctx.fillStyle = '#1a1a1a';
        ctx.fillRect(0, 0, 320, 240);
        ctx.fillStyle = '#ff6600';
        ctx.fillText('MOCK ' + Date.now() % 10000, 60, 120);
      }, 500);
      const stream = canvas.captureStream(10);
      return stream;
    }
    return origGetUserMedia(constraints);
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
