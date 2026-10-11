/**
 * Global — Explore the Lunar Crater
 * Interactive 3D Photorealistic Moon Engine & Animations
 * Built with Three.js — Photorealistic Photographic Lunar Texture
 */

// --- 1. DEEP SPACE PARTICLE STARFIELD ---
(function initStarfield() {
  const canvas = document.getElementById('starfield-canvas');
  if (!canvas) return;
  const ctx = canvas.getContext('2d');
  let width, height;
  let stars = [];
  const STAR_COUNT = 140;

  function resize() {
    width = canvas.width = window.innerWidth;
    height = canvas.height = window.innerHeight;
    stars = [];
    for (let i = 0; i < STAR_COUNT; i++) {
      stars.push({
        x: Math.random() * width,
        y: Math.random() * height,
        radius: Math.random() * 1.1 + 0.3,
        alpha: Math.random() * 0.6 + 0.2,
        speed: Math.random() * 0.01 + 0.003,
        phase: Math.random() * Math.PI * 2
      });
    }
  }

  window.addEventListener('resize', resize);
  resize();

  function animateStars(time) {
    ctx.clearRect(0, 0, width, height);
    for (let i = 0; i < stars.length; i++) {
      const s = stars[i];
      const brightness = s.alpha + Math.sin(time * s.speed + s.phase) * 0.2;
      const clampedAlpha = Math.max(0.1, Math.min(0.85, brightness));

      ctx.beginPath();
      ctx.arc(s.x, s.y, s.radius, 0, Math.PI * 2);
      ctx.fillStyle = `rgba(255, 255, 255, ${clampedAlpha})`;
      ctx.fill();
    }
    requestAnimationFrame(animateStars);
  }
  requestAnimationFrame(animateStars);
})();


// --- 2. THREE.JS 3D PHOTOREALISTIC MOON ENGINE ---
(function initMoon3D() {
  const container = document.getElementById('moon-canvas-wrapper');
  if (!container) return;

  // Scene & Camera
  const scene = new THREE.Scene();
  
  let aspect = container.clientWidth / container.clientHeight;
  const camera = new THREE.PerspectiveCamera(40, aspect, 0.1, 1000);
  camera.position.set(0, 0, 7.2);

  // High-performance WebGL Renderer
  const renderer = new THREE.WebGLRenderer({
    antialias: true,
    alpha: true,
    powerPreference: 'high-performance'
  });
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
  renderer.toneMapping = THREE.ACESFilmicToneMapping;
  renderer.toneMappingExposure = 1.05;
  renderer.outputEncoding = THREE.sRGBEncoding;
  container.appendChild(renderer.domElement);

  // OrbitControls for smooth drag & inspection
  const controls = new THREE.OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.dampingFactor = 0.05;
  controls.enableZoom = true;
  controls.minDistance = 4.8;
  controls.maxDistance = 11.0;
  controls.enablePan = false;
  controls.rotateSpeed = 0.75;

  // Realistic Lighting Setup (Photographic Full Moon balance)
  // 1. Direct Sun Key Light from front-right
  const sunLight = new THREE.DirectionalLight(0xffffff, 2.0);
  sunLight.position.set(5, 2.5, 7);
  scene.add(sunLight);

  // 2. Soft Earthshine Fill Light
  const fillLight = new THREE.DirectionalLight(0xa5b8d0, 0.45);
  fillLight.position.set(-5, -1, 3);
  scene.add(fillLight);

  // 3. Ambient Light for balanced photographic shadows
  const ambientLight = new THREE.AmbientLight(0x282c35, 0.4);
  scene.add(ambientLight);

  // High-Detail Moon Sphere Geometry
  const moonRadius = 2.45;
  const moonGeometry = new THREE.SphereGeometry(moonRadius, 96, 96);

  const moonGroup = new THREE.Group();
  scene.add(moonGroup);

  // Create clean placeholder material
  const placeholderMat = new THREE.MeshStandardMaterial({
    color: 0x9fa4ad,
    roughness: 0.95,
    metalness: 0.0
  });

  const moonMesh = new THREE.Mesh(moonGeometry, placeholderMat);
  moonMesh.rotation.y = -0.65 * Math.PI; // Center the near-side photo with Tycho & maria straight to front
  moonGroup.add(moonMesh);

  // Subtle lunar limb glow (gentle atmospheric edge)
  const haloGeo = new THREE.SphereGeometry(moonRadius * 1.012, 64, 64);
  const haloMat = new THREE.ShaderMaterial({
    vertexShader: `
      varying vec3 vNormal;
      void main() {
        vNormal = normalize(normalMatrix * normal);
        gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
      }
    `,
    fragmentShader: `
      varying vec3 vNormal;
      void main() {
        float intensity = pow(0.7 - dot(vNormal, vec3(0.0, 0.0, 1.0)), 3.2);
        gl_FragColor = vec4(0.85, 0.9, 1.0, intensity * 0.22);
      }
    `,
    blending: THREE.AdditiveBlending,
    side: THREE.BackSide,
    transparent: true
  });
  const haloMesh = new THREE.Mesh(haloGeo, haloMat);
  moonGroup.add(haloMesh);

  // Texture Loader & Apply Clean Photographic Material
  const textureLoader = new THREE.TextureLoader();

  function applyPhotorealisticTexture(texture) {
    texture.wrapS = THREE.RepeatWrapping;
    texture.wrapT = THREE.ClampToEdgeWrapping;
    texture.encoding = THREE.sRGBEncoding;

    // Smooth, realistic lunar regolith: NO artificial harsh bumpy craters
    const photoRealisticMaterial = new THREE.MeshStandardMaterial({
      map: texture,
      roughness: 0.94,
      metalness: 0.01
    });

    moonMesh.material = photoRealisticMaterial;
    moonMesh.material.needsUpdate = true;
  }

  // Load Real Texture (Prioritize Base64 to ensure instant zero-CORS loading)
  if (typeof MOON_TEXTURE_B64 !== 'undefined' && MOON_TEXTURE_B64) {
    textureLoader.load(MOON_TEXTURE_B64, (tex) => {
      applyPhotorealisticTexture(tex);
    });
  } else {
    textureLoader.load(
      './assets/real_lunar_equirectangular.jpg',
      (tex) => applyPhotorealisticTexture(tex),
      undefined,
      () => {
        textureLoader.load('./assets/moon_map.jpg', (tex) => {
          applyPhotorealisticTexture(tex);
        });
      }
    );
  }

  // --- 3. INTERACTIVE LANDING MARKER (SHIV SHAKTI POINT) ---
  const markersGroup = new THREE.Group();
  moonGroup.add(markersGroup);

  function latLongToVector3(lat, lon, radius) {
    const phi = (90 - lat) * (Math.PI / 180);
    const theta = (lon + 180) * (Math.PI / 180);
    const x = -(radius * Math.sin(phi) * Math.cos(theta));
    const z = radius * Math.sin(phi) * Math.sin(theta);
    const y = radius * Math.cos(phi);
    return new THREE.Vector3(x, y, z);
  }

  // Shiv Shakti Point Landing Site Marker
  const landingPos = latLongToVector3(-69.37, 32.35, moonRadius + 0.015);
  
  const ringGeo = new THREE.RingGeometry(0.045, 0.065, 32);
  const ringMat = new THREE.MeshBasicMaterial({ color: 0x00f2fe, side: THREE.DoubleSide });
  const landingRing = new THREE.Mesh(ringGeo, ringMat);
  landingRing.position.copy(landingPos);
  landingRing.lookAt(landingPos.clone().multiplyScalar(2));
  markersGroup.add(landingRing);

  const dotGeo = new THREE.SphereGeometry(0.02, 16, 16);
  const dotMat = new THREE.MeshBasicMaterial({ color: 0xffffff });
  const landingDot = new THREE.Mesh(dotGeo, dotMat);
  landingDot.position.copy(landingPos);
  markersGroup.add(landingDot);

  // Hidden by default for clean natural photo appearance, toggled via button
  markersGroup.visible = false;

  // --- 4. SMOOTH CONTINUOUS 3D ROTATION ---
  let isRotating = true;
  const baseRotationSpeed = 0.0018; // Elegant, slow planetary spin
  let targetRotationX = 0;
  let targetRotationY = 0;

  // Gentle Mouse Parallax
  window.addEventListener('mousemove', (e) => {
    const mouseX = (e.clientX / window.innerWidth) * 2 - 1;
    const mouseY = -(e.clientY / window.innerHeight) * 2 + 1;
    targetRotationX = mouseY * 0.08;
    targetRotationY = mouseX * 0.1;
  });

  // Toggle Rotation Button HUD
  const rotBtn = document.getElementById('rotation-toggle-btn');
  const rotStatusText = document.getElementById('rotation-status-text');
  const rotDot = document.querySelector('.hud-status-dot');

  if (rotBtn) {
    rotBtn.addEventListener('click', () => {
      isRotating = !isRotating;
      if (isRotating) {
        rotStatusText.textContent = '3D Rotation: Active';
        rotDot.classList.add('active');
      } else {
        rotStatusText.textContent = '3D Rotation: Paused';
        rotDot.classList.remove('active');
      }
    });
  }

  // Toggle Interactive Markers Button
  const exploreBtn = document.getElementById('explore-btn');
  if (exploreBtn) {
    exploreBtn.addEventListener('click', () => {
      markersGroup.visible = !markersGroup.visible;
      exploreBtn.style.borderColor = markersGroup.visible ? '#00f2fe' : 'rgba(255,255,255,0.12)';
      exploreBtn.style.color = markersGroup.visible ? '#00f2fe' : '#a1a1aa';
    });
  }

  // Clock for smooth animation
  const clock = new THREE.Clock();

  function animate() {
    requestAnimationFrame(animate);

    // Rotate Moon continuously around polar axis
    if (isRotating) {
      moonMesh.rotation.y += baseRotationSpeed;
    }

    // Gentle pulse on Shiv Shakti Landing Marker when active
    if (markersGroup.visible) {
      const time = clock.getElapsedTime();
      const pulseScale = 1.0 + Math.sin(time * 3.5) * 0.22;
      landingRing.scale.set(pulseScale, pulseScale, pulseScale);
    }

    // Subtle gentle parallax tilt
    moonGroup.rotation.x += (targetRotationX - moonGroup.rotation.x) * 0.035;
    moonGroup.rotation.z += (targetRotationY - moonGroup.rotation.z) * 0.035;

    controls.update();
    renderer.render(scene, camera);
  }
  animate();

  // Resize listener
  function onWindowResize() {
    const w = container.clientWidth;
    const h = container.clientHeight;
    camera.aspect = w / h;
    camera.updateProjectionMatrix();
    renderer.setSize(w, h);
  }
  window.addEventListener('resize', onWindowResize);

})();
