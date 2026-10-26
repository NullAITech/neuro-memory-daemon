/**
 * ==============================================================================
 * 🌌 NEBULA ENGINE — 3D Volumetric Synaptic Substrate & Plasma Memory Universe
 * Pure WebGL (Three.js + OrbitControls) with Zero External Dependencies.
 *
 * Architecture:
 * 1. Volumetric Cosmic Nebula with 3,500+ harmonic stardust particles.
 * 2. 5 Hyperfocused 3D Galaxy Clusters:
 *    - Agents Galaxy (Antigravity, Grok, Claude, Hermes, Cursor, Sentinel, Ollama)
 *    - Tools Galaxy (Bash CLI, AST parser, Math pillar, Code tools)
 *    - Security Galaxy (Guardrails, Sandboxes, Entropy, Crypto, Auth)
 *    - System Galaxy (Kernel, SQLite WAL, Telemetry, Memory substrate)
 *    - Living Minds Galaxy (Civilization colonies, Emergent dialogues)
 * 3. Curved Bezier Synaptic Filaments with STDP plastic weight modulation.
 * 4. "Plasma Liquid Air" Action Potential Pulses flowing along biological axons.
 * 5. Real-time Live Brain Triggers via SSE /api/stream and interactive firing.
 * ==============================================================================
 */

(function () {
  'use strict';

  // Galaxy Cluster Coordinate Offsets and Color Palette
  const GALAXY_CLUSTERS = {
    agents: {
      name: 'Agents Galaxy',
      id: 'agents',
      center: new THREE.Vector3(-220, 60, -80),
      color: 0xD4AF37, // Sovereign Gold
      hex: '#D4AF37',
      auraColor: 0xF5E6AB,
      description: 'Antigravity, Grok, Claude, Hermes, Cursor, Sentinel, Ollama',
    },
    tools: {
      name: 'Tools Galaxy',
      id: 'tools',
      center: new THREE.Vector3(220, 80, -100),
      color: 0x00E5FF, // Electric Cyan
      hex: '#00E5FF',
      auraColor: 0x80F0FF,
      description: 'Bash CLI, AST Parser, Network, Math Pillar, Python Tools',
    },
    security: {
      name: 'Security Galaxy',
      id: 'security',
      center: new THREE.Vector3(180, -120, 140),
      color: 0xFF3366, // Crimson Laser
      hex: '#FF3366',
      auraColor: 0xFF809B,
      description: 'Memory Guardrails, Sandboxes, Entropy, Zero-Egress, Crypto',
    },
    system: {
      name: 'System Galaxy',
      id: 'system',
      center: new THREE.Vector3(-180, -130, 100),
      color: 0xA855F7, // Deep Violet
      hex: '#A855F7',
      auraColor: 0xD8B4FE,
      description: 'ZothOS Kernel, SQLite WAL, Process Tree, Hardware Telemetry',
    },
      living_minds: {
        name: 'Living Minds Galaxy',
        id: 'living_minds',
        center: new THREE.Vector3(0, 160, 80),
        color: 0x10B981, // Emerald Biome
        hex: '#10B981',
        auraColor: 0x6EE7B7,
        description: 'Civilization Colonies, Epistemic Reflections, Autonomous Mind',
      },
      obsidian: {
        name: 'Obsidian Second Brain',
        id: 'obsidian',
        center: new THREE.Vector3(0, -145, 165),
        color: 0xE879F9, // Radiant Fuchsia-Amethyst
        hex: '#E879F9',
        auraColor: 0xF5D0FE,
        description: 'Obsidian Vault MOCs, JSON Canvas (.canvas), Bases (.base) & 7 Agent Skills',
      },
    };

  // Helper to generate soft radial glow particle sprite in-memory (no external image assets)
  function createGlowTexture(colorStr, radius = 64) {
    const canvas = document.createElement('canvas');
    canvas.width = radius * 2;
    canvas.height = radius * 2;
    const ctx = canvas.getContext('2d');

    const grad = ctx.createRadialGradient(radius, radius, 0, radius, radius, radius);
    grad.addColorStop(0, colorStr || '#ffffff');
    grad.addColorStop(0.2, colorStr || '#ffffff');
    grad.addColorStop(0.6, 'rgba(255,255,255,0.2)');
    grad.addColorStop(1, 'rgba(0,0,0,0)');

    ctx.fillStyle = grad;
    ctx.fillRect(0, 0, radius * 2, radius * 2);

    const texture = new THREE.CanvasTexture(canvas);
    texture.needsUpdate = true;
    return texture;
  }

  // Text billboard sprite generator for floating 3D labels
  function createTextSprite(text, colorStr = '#D4AF37', fontSize = 28) {
    const canvas = document.createElement('canvas');
    canvas.width = 512;
    canvas.height = 128;
    const ctx = canvas.getContext('2d');

    ctx.clearRect(0, 0, 512, 128);
    ctx.font = `bold ${fontSize}px "Google Sans", "Segoe UI", sans-serif`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';

    // Text shadow for high contrast over nebula
    ctx.shadowColor = 'rgba(0, 0, 0, 0.9)';
    ctx.shadowBlur = 10;
    ctx.fillStyle = colorStr;
    ctx.fillText(text, 256, 64);

    const texture = new THREE.CanvasTexture(canvas);
    const material = new THREE.SpriteMaterial({
      map: texture,
      transparent: true,
      depthWrite: false,
    });
    const sprite = new THREE.Sprite(material);
    sprite.scale.set(60, 15, 1);
    return sprite;
  }

  // Pure Web Audio API Synthesizer for Bio-Resonant Synaptic Feedback (Zero Files/CDNs)
  class BioAudioSynthesizer {
    constructor() {
      this.ctx = null;
      this.enabled = false;
    }

    ensureContext() {
      if (!this.ctx && typeof (window.AudioContext || window.webkitAudioContext) !== 'undefined') {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        this.ctx = new AudioCtx();
      }
      if (this.ctx && this.ctx.state === 'suspended') {
        this.ctx.resume().catch(() => {});
      }
    }

    playActionPotential(freq = 528) {
      if (!this.enabled) return;
      try {
        this.ensureContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        const osc = this.ctx.createOscillator();
        const gain = this.ctx.createGain();

        osc.type = 'sine';
        osc.frequency.setValueAtTime(freq * 0.85, now);
        osc.frequency.exponentialRampToValueAtTime(freq * 1.3, now + 0.08);

        gain.gain.setValueAtTime(0.06, now);
        gain.gain.exponentialRampToValueAtTime(0.0001, now + 0.16);

        osc.connect(gain);
        gain.connect(this.ctx.destination);

        osc.start(now);
        osc.stop(now + 0.18);
      } catch (e) {}
    }

    playSleepRipple() {
      if (!this.enabled) return;
      try {
        this.ensureContext();
        if (!this.ctx) return;
        const now = this.ctx.currentTime;
        [432, 528, 648].forEach((freq, idx) => {
          const osc = this.ctx.createOscillator();
          const gain = this.ctx.createGain();
          osc.type = 'triangle';
          osc.frequency.setValueAtTime(freq, now + idx * 0.1);

          gain.gain.setValueAtTime(0.035, now + idx * 0.1);
          gain.gain.exponentialRampToValueAtTime(0.0001, now + idx * 0.1 + 0.8);

          osc.connect(gain);
          gain.connect(this.ctx.destination);

          osc.start(now + idx * 0.1);
          osc.stop(now + idx * 0.1 + 0.85);
        });
      } catch (e) {}
    }

    toggle() {
      this.enabled = !this.enabled;
      if (this.enabled) this.ensureContext();
      return this.enabled;
    }
  }

  class NebulaUniverse {
    constructor(containerElement) {
      this.container = containerElement;
      this.scene = null;
      this.camera = null;
      this.renderer = null;
      this.controls = null;
      this.raycaster = new THREE.Raycaster();
      this.mouse = new THREE.Vector2();

      this.audio = new BioAudioSynthesizer();
      this.pointerDownPos = { x: 0, y: 0 };
      this.pointerDownTime = 0;

      this.stardustPoints = null;
      this.stardustPositions = null;
      this.galaxyCores = [];
      this.nodeMeshes = new Map(); // id -> THREE.Mesh
      this.filamentCurves = []; // list of { curve, line, sourceId, targetId, weight }
      this.plasmaPulses = []; // active traveling action potentials

      this.cameraTarget = new THREE.Vector3(0, 0, 0);
      this.cameraLookAt = new THREE.Vector3(0, 0, 0);
      this.isGlidingCamera = false;
      this.glideStartTime = 0;
      this.glideStartPos = new THREE.Vector3();
      this.glideEndPos = new THREE.Vector3();
      this.glideStartLook = new THREE.Vector3();
      this.glideEndLook = new THREE.Vector3();

      this.clock = new THREE.Clock();
      this.hoveredNode = null;
      this.selectedNode = null;
      this.sseSource = null;
      this.stats = {
        totalEngrams: 0,
        totalSynapses: 0,
        activePulses: 0,
        actionFrequency: 1.2,
      };

      this.onNodeClickCallback = null;
      this.onNodeHoverCallback = null;

      this.init();
    }

    init() {
      const width = this.container.clientWidth || 800;
      const height = this.container.clientHeight || 500;

      // 1. Scene & Background
      this.scene = new THREE.Scene();
      this.scene.fog = new THREE.FogExp2(0x08080B, 0.0012);

      // 2. Camera
      this.camera = new THREE.PerspectiveCamera(50, width / height, 1, 3000);
      this.camera.position.set(0, 180, 520);
      this.camera.lookAt(0, 0, 0);

      // 3. Renderer
      this.renderer = new THREE.WebGLRenderer({
        antialias: true,
        alpha: true,
        powerPreference: 'high-performance',
      });
      this.renderer.setSize(width, height);
      this.renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      this.renderer.setClearColor(0x08080B, 1);
      this.container.appendChild(this.renderer.domElement);
      this.renderer.domElement.id = 'nebula-3d-canvas';
      this.renderer.domElement.style.width = '100%';
      this.renderer.domElement.style.height = '100%';
      this.renderer.domElement.style.display = 'block';

      // 4. OrbitControls
      if (typeof THREE.OrbitControls === 'function') {
        this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
        this.controls.enableDamping = true;
        this.controls.dampingFactor = 0.06;
        this.controls.rotateSpeed = 0.6;
        this.controls.zoomSpeed = 0.8;
        this.controls.maxDistance = 1200;
        this.controls.minDistance = 60;
        this.controls.autoRotate = true;
        this.controls.autoRotateSpeed = 0.4;
      }

      // 5. Lights
      const ambientLight = new THREE.AmbientLight(0x222233, 1.2);
      this.scene.add(ambientLight);

      const centerLight = new THREE.PointLight(0xD4AF37, 2.0, 800);
      centerLight.position.set(0, 0, 0);
      this.scene.add(centerLight);

      const cyanFillLight = new THREE.PointLight(0x00E5FF, 1.5, 600);
      cyanFillLight.position.set(200, 100, 200);
      this.scene.add(cyanFillLight);

      const purpleFillLight = new THREE.PointLight(0x8A2BE2, 1.5, 600);
      purpleFillLight.position.set(-200, -100, -200);
      this.scene.add(purpleFillLight);

      // 6. Build Stardust, Galaxy Clusters & Interactive 3D Netrunner Core Model
      this.buildStardustField();
      this.buildGalaxyClusters();
      this.buildNetrunnerCoreModel();

      // 7. Event Listeners
      window.addEventListener('resize', () => this.onWindowResize());
      this.renderer.domElement.addEventListener('mousemove', (e) => this.onMouseMove(e));
      this.renderer.domElement.addEventListener('pointerdown', (e) => {
        this.pointerDownPos = { x: e.clientX, y: e.clientY };
        this.pointerDownTime = performance.now();
      });
      this.renderer.domElement.addEventListener('pointerup', (e) => {
        const dx = e.clientX - this.pointerDownPos.x;
        const dy = e.clientY - this.pointerDownPos.y;
        const dist = Math.hypot(dx, dy);
        const elapsed = performance.now() - this.pointerDownTime;
        if (dist < 8 && elapsed < 500) {
          this.handleNodeClick(e);
        }
      });

      // 8. Animation Loop
      this.animate();

      // 9. Wire SSE Stream
      this.connectSSE();
    }

    buildStardustField() {
      const particleCount = 3800;
      const geometry = new THREE.BufferGeometry();
      const positions = new Float32Array(particleCount * 3);
      const colors = new Float32Array(particleCount * 3);
      const sizes = new Float32Array(particleCount);

      const palette = [
        new THREE.Color(0xD4AF37), // Gold
        new THREE.Color(0xF5E6AB), // Pale Gold
        new THREE.Color(0x00E5FF), // Cyan
        new THREE.Color(0x8A2BE2), // Violet
        new THREE.Color(0x10B981), // Emerald
        new THREE.Color(0x4A6CF7), // Royal Blue
      ];

      for (let i = 0; i < particleCount; i++) {
        // Spherical distribution with denser inner cosmic halo
        const radius = Math.pow(Math.random(), 0.7) * 700;
        const theta = Math.random() * Math.PI * 2;
        const phi = Math.acos((Math.random() * 2) - 1);

        const x = radius * Math.sin(phi) * Math.cos(theta);
        const y = (radius * Math.sin(phi) * Math.sin(theta)) * 0.65; // flattened galactic disc
        const z = radius * Math.cos(phi);

        positions[i * 3] = x;
        positions[i * 3 + 1] = y;
        positions[i * 3 + 2] = z;

        const col = palette[Math.floor(Math.random() * palette.length)];
        colors[i * 3] = col.r;
        colors[i * 3 + 1] = col.g;
        colors[i * 3 + 2] = col.b;

        sizes[i] = Math.random() * 3.5 + 1.2;
      }

      geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));
      geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));

      this.stardustPositions = positions;

      const particleTexture = createGlowTexture('rgba(255,255,255,0.95)', 32);
      const material = new THREE.PointsMaterial({
        size: 3.5,
        map: particleTexture,
        vertexColors: true,
        transparent: true,
        opacity: 0.75,
        blending: THREE.AdditiveBlending,
        depthWrite: false,
      });

      this.stardustPoints = new THREE.Points(geometry, material);
      this.scene.add(this.stardustPoints);
    }

    buildGalaxyClusters() {
      const coreTexture = createGlowTexture('rgba(255,255,255,1)', 64);

      Object.values(GALAXY_CLUSTERS).forEach((galaxy) => {
        // Glowing Core Sprite
        const mat = new THREE.SpriteMaterial({
          map: coreTexture,
          color: galaxy.color,
          transparent: true,
          opacity: 0.65,
          blending: THREE.AdditiveBlending,
          depthWrite: false,
        });
        const sprite = new THREE.Sprite(mat);
        sprite.position.copy(galaxy.center);
        sprite.scale.set(70, 70, 1);
        this.scene.add(sprite);

        // Core Halo ring
        const ringGeo = new THREE.RingGeometry(25, 27, 48);
        const ringMat = new THREE.MeshBasicMaterial({
          color: galaxy.color,
          side: THREE.DoubleSide,
          transparent: true,
          opacity: 0.35,
          blending: THREE.AdditiveBlending,
        });
        const ring = new THREE.Mesh(ringGeo, ringMat);
        ring.position.copy(galaxy.center);
        ring.rotation.x = Math.PI / 2;
        this.scene.add(ring);

        // Floating 3D Title Label
        const titleSprite = createTextSprite(galaxy.name, galaxy.hex, 32);
        titleSprite.position.set(galaxy.center.x, galaxy.center.y + 40, galaxy.center.z);
        this.scene.add(titleSprite);

        this.galaxyCores.push({
          sprite,
          ring,
          title: titleSprite,
          galaxy,
        });
      });
    }

    buildNetrunnerCoreModel() {
      const coreGroup = new THREE.Group();
      coreGroup.position.set(0, 0, 0);

      // 1. Cybernetic Icosahedral Brain Cortex (Wireframe + Inner Emissive Core)
      const brainGeo = new THREE.IcosahedronGeometry(26, 2);
      const brainWireMat = new THREE.MeshBasicMaterial({
        color: 0x00E5FF,
        wireframe: true,
        transparent: true,
        opacity: 0.45,
        blending: THREE.AdditiveBlending,
      });
      const brainWireMesh = new THREE.Mesh(brainGeo, brainWireMat);
      coreGroup.add(brainWireMesh);

      const innerCoreGeo = new THREE.IcosahedronGeometry(14, 1);
      const innerCoreMat = new THREE.MeshStandardMaterial({
        color: 0xD4AF37,
        emissive: 0xD4AF37,
        emissiveIntensity: 0.85,
        roughness: 0.2,
        metalness: 0.9,
      });
      const innerCoreMesh = new THREE.Mesh(innerCoreGeo, innerCoreMat);
      innerCoreMesh.userData = {
        isNetrunnerCore: true,
        nodeData: {
          id: 'netrunner-core-0',
          label: 'NETRUNNER CYBER-CORTEX CORE',
          text: 'Sovereign 3-Factor STDP Neural Cortex & Obsidian Second Brain Bridge. Click to fire global Hippocampal Sharp-Wave Ripple (SWR) across all 6 galaxy clusters.',
          category: 'architecture',
          agent_id: 'azoth',
          importance: 2.0,
          access_count: 99,
          tags: ['netrunner', 'stdp', 'cortex', 'obsidian', 'hippocampus'],
        },
        galaxy: { name: 'Netrunner Cyber-Cortex', hex: '#D4AF37', color: 0xD4AF37 },
        baseColor: 0xD4AF37,
        baseRadius: 1.0,
      };
      coreGroup.add(innerCoreMesh);

      // 2. Glowing Cybernetic Optic Visor Arc
      const visorGeo = new THREE.TorusGeometry(28, 1.4, 12, 48, Math.PI * 0.85);
      const visorMat = new THREE.MeshBasicMaterial({
        color: 0x00E5FF,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });
      const visorMesh = new THREE.Mesh(visorGeo, visorMat);
      visorMesh.rotation.x = Math.PI / 2;
      visorMesh.rotation.z = -Math.PI * 0.42;
      visorMesh.position.y = 4;
      coreGroup.add(visorMesh);

      // 3. Articulated Cybernetic Spinal Column (7 Cervical/Thoracic Neural Vertebrae)
      const spineGroup = new THREE.Group();
      for (let i = 0; i < 7; i++) {
        const radius = 8 - i * 0.7;
        const discGeo = new THREE.CylinderGeometry(radius, radius * 0.85, 3.2, 16);
        const discMat = new THREE.MeshStandardMaterial({
          color: i % 2 === 0 ? 0xD4AF37 : 0x00E5FF,
          emissive: i % 2 === 0 ? 0xD4AF37 : 0x00E5FF,
          emissiveIntensity: 0.5,
          metalness: 0.8,
          roughness: 0.3,
        });
        const disc = new THREE.Mesh(discGeo, discMat);
        disc.position.y = -32 - i * 7.5;
        spineGroup.add(disc);
      }
      coreGroup.add(spineGroup);

      // 4. Counter-Rotating Gyroscopic STDP Gimbal Rings
      const gimbal1Geo = new THREE.TorusGeometry(42, 0.65, 16, 96);
      const gimbal1Mat = new THREE.MeshBasicMaterial({
        color: 0xD4AF37,
        transparent: true,
        opacity: 0.65,
        blending: THREE.AdditiveBlending,
      });
      const gimbal1 = new THREE.Mesh(gimbal1Geo, gimbal1Mat);
      coreGroup.add(gimbal1);

      const gimbal2Geo = new THREE.TorusGeometry(52, 0.55, 16, 96);
      const gimbal2Mat = new THREE.MeshBasicMaterial({
        color: 0x00E5FF,
        transparent: true,
        opacity: 0.45,
        blending: THREE.AdditiveBlending,
      });
      const gimbal2 = new THREE.Mesh(gimbal2Geo, gimbal2Mat);
      gimbal2.rotation.x = Math.PI / 3;
      coreGroup.add(gimbal2);

      const gimbal3Geo = new THREE.TorusGeometry(62, 0.5, 16, 96);
      const gimbal3Mat = new THREE.MeshBasicMaterial({
        color: 0xE879F9,
        transparent: true,
        opacity: 0.35,
        blending: THREE.AdditiveBlending,
      });
      const gimbal3 = new THREE.Mesh(gimbal3Geo, gimbal3Mat);
      gimbal3.rotation.y = Math.PI / 4;
      coreGroup.add(gimbal3);

      // 5. Floating Label above the Netrunner Cyber-Cortex
      const coreLabel = createTextSprite('⚡ NETRUNNER CYBER-CORTEX', '#00E5FF', 28);
      coreLabel.position.set(0, 56, 0);
      coreGroup.add(coreLabel);

      this.scene.add(coreGroup);
      this.netrunnerCore = {
        group: coreGroup,
        brainWireMesh,
        innerCoreMesh,
        visorMesh,
        spineGroup,
        gimbal1,
        gimbal2,
        gimbal3,
      };
    }

    // Determine which 3D galaxy cluster an engram belongs to
    determineGalaxy(node) {
      const text = (node.label || node.text || '').toLowerCase();
      const cat = (node.category || '').toLowerCase();
      const tags = (node.tags || []).map(t => String(t).toLowerCase());
      const agentId = (node.agent_id || '').toLowerCase();

      // 0. Obsidian Second Brain Galaxy
      if (
        cat === 'obsidian' || cat === 'vault' || cat === 'second-brain' ||
        agentId.includes('obsidian') ||
        tags.some(t => ['obsidian', 'vault', 'moc', 'wikilink', 'canvas', 'json-canvas', 'obsidian-bases', 'second-brain', 'defuddle', 'knap'].includes(t)) ||
        text.includes('obsidian') || text.includes('[[') || text.includes('.canvas') || text.includes('.base') || text.includes('second brain')
      ) {
        return GALAXY_CLUSTERS.obsidian;
      }

      // 1. Agents Galaxy
      if (
        agentId.includes('antigravity') || agentId.includes('grok') || agentId.includes('claude') ||
        agentId.includes('hermes') || agentId.includes('cursor') || agentId.includes('sentinel') ||
        tags.some(t => ['agent', 'subagent', 'antigravity', 'grok', 'claude', 'hermes', 'llm', 'mcp'].includes(t)) ||
        text.includes('agent') || text.includes('grok') || text.includes('antigravity')
      ) {
        return GALAXY_CLUSTERS.agents;
      }

      // 2. Tools Galaxy
      if (
        cat === 'tool' || cat === 'procedure' ||
        tags.some(t => ['tool', 'bash', 'ast', 'git', 'cli', 'math', 'code', 'regex', 'curl', 'compiler'].includes(t)) ||
        text.includes('command') || text.includes('bash') || text.includes('script')
      ) {
        return GALAXY_CLUSTERS.tools;
      }

      // 3. Security Galaxy
      if (
        cat === 'security' ||
        tags.some(t => ['security', 'sandbox', 'entropy', 'auth', 'jwt', 'crypto', 'firewall', 'guardrail', 'egress'].includes(t)) ||
        text.includes('security') || text.includes('vulnerability') || text.includes('cipher')
      ) {
        return GALAXY_CLUSTERS.security;
      }

      // 4. System Galaxy
      if (
        cat === 'architecture' || cat === 'debug' ||
        tags.some(t => ['kernel', 'sqlite', 'wal', 'storage', 'process', 'hardware', 'daemon', 'system', 'zothos'].includes(t)) ||
        text.includes('kernel') || text.includes('database') || text.includes('systemd')
      ) {
        return GALAXY_CLUSTERS.system;
      }

      // 5. Living Minds Galaxy (Default for semantic, reflections, dialogues)
      return GALAXY_CLUSTERS.living_minds;
    }

    loadGraph(nodes, edges) {
      // Clear existing node meshes and filaments
      this.nodeMeshes.forEach(mesh => this.scene.remove(mesh));
      this.nodeMeshes.clear();

      this.filamentCurves.forEach(item => this.scene.remove(item.line));
      this.filamentCurves = [];

      this.plasmaPulses.forEach(pulse => {
        if (pulse.mesh) this.scene.remove(pulse.mesh);
      });
      this.plasmaPulses = [];

      this.stats.totalEngrams = nodes.length;
      this.stats.totalSynapses = edges.length;

      const sphereGeo = new THREE.SphereGeometry(1, 24, 24);

      // 1. Position and instantiate Node Meshes in 3D Galaxy Clusters
      nodes.forEach((node, idx) => {
        const galaxy = this.determineGalaxy(node);
        const clusterCenter = galaxy.center;

        // Pseudo-random deterministic spherical offset within galaxy cluster
        const seedVal = (idx + 1) * 9301 + 49297;
        const angle1 = (seedVal % 1000) / 1000 * Math.PI * 2;
        const angle2 = ((seedVal * 7) % 1000) / 1000 * Math.PI - (Math.PI / 2);
        const dist = 20 + (((seedVal * 13) % 1000) / 1000) * 85;

        const posX = clusterCenter.x + Math.cos(angle1) * Math.cos(angle2) * dist;
        const posY = clusterCenter.y + Math.sin(angle2) * (dist * 0.75);
        const posZ = clusterCenter.z + Math.sin(angle1) * Math.cos(angle2) * dist;

        // Node size based on importance and access count
        const importance = typeof node.importance === 'number' ? node.importance : 1.0;
        const accessCount = node.access_count || 1;
        const nodeRadius = Math.max(3.0, Math.min(10.0, (3.2 * importance) + Math.log1p(accessCount) * 0.8));

        const mat = new THREE.MeshStandardMaterial({
          color: galaxy.color,
          emissive: galaxy.color,
          emissiveIntensity: 0.55,
          roughness: 0.25,
          metalness: 0.8,
        });

        const mesh = new THREE.Mesh(sphereGeo, mat);
        mesh.scale.set(nodeRadius, nodeRadius, nodeRadius);
        mesh.position.set(posX, posY, posZ);
        mesh.userData = {
          nodeData: node,
          galaxy: galaxy,
          baseColor: galaxy.color,
          baseRadius: nodeRadius,
          isPulsing: false,
        };

        this.scene.add(mesh);
        this.nodeMeshes.set(String(node.id), mesh);
      });

      // 2. Build Curved Bezier Synaptic Filaments
      const seenPairs = new Set();
      const filamentMatWeak = new THREE.LineBasicMaterial({
        color: 0x4A6CF7,
        transparent: true,
        opacity: 0.35,
        blending: THREE.AdditiveBlending,
      });
      const filamentMatMed = new THREE.LineBasicMaterial({
        color: 0x00E5FF,
        transparent: true,
        opacity: 0.65,
        blending: THREE.AdditiveBlending,
      });
      const filamentMatStrong = new THREE.LineBasicMaterial({
        color: 0xFFD700,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });

      edges.forEach((edge) => {
        const srcMesh = this.nodeMeshes.get(String(edge.source));
        const tgtMesh = this.nodeMeshes.get(String(edge.target));
        if (!srcMesh || !tgtMesh) return;

        const pairKey = [String(edge.source), String(edge.target)].sort().join('<->');
        if (seenPairs.has(pairKey)) return;
        seenPairs.add(pairKey);

        const p1 = srcMesh.position;
        const p2 = tgtMesh.position;

        // Quadratic Bezier midpoint arched outward
        const midPoint = new THREE.Vector3().addVectors(p1, p2).multiplyScalar(0.5);
        const dist = p1.distanceTo(p2);
        const arcHeight = Math.min(60, dist * 0.25);
        midPoint.y += arcHeight; // lift upward

        const curve = new THREE.QuadraticBezierCurve3(p1, midPoint, p2);
        const points = curve.getPoints(24);
        const lineGeo = new THREE.BufferGeometry().setFromPoints(points);

        const weight = typeof edge.weight === 'number' ? edge.weight : 0.2;
        let lineMat = filamentMatWeak;
        if (weight >= 0.6) lineMat = filamentMatStrong;
        else if (weight >= 0.3) lineMat = filamentMatMed;

        const line = new THREE.Line(lineGeo, lineMat);
        this.scene.add(line);

        this.filamentCurves.push({
          curve,
          line,
          sourceId: String(edge.source),
          targetId: String(edge.target),
          weight,
          srcPos: p1,
          tgtPos: p2,
        });

        // Spawn ambient plasma action potential pulses along strong synapses
        if (weight >= 0.4 || Math.random() < 0.25) {
          this.spawnPlasmaPulse(curve, weight, lineMat.color);
        }
      });

      this.updateHudStats();
    }

    spawnPlasmaPulse(curve, weight = 0.5, color = 0xFFD700, speedMultiplier = 1.0) {
      const pulseGeo = new THREE.SphereGeometry(1.4, 12, 12);
      const pulseMat = new THREE.MeshBasicMaterial({
        color: color,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });
      const mesh = new THREE.Mesh(pulseGeo, pulseMat);

      const pulse = {
        curve,
        mesh,
        t: Math.random(),
        speed: (0.12 + (weight * 0.18)) * speedMultiplier,
        size: 1.4 + (weight * 1.6),
      };
      mesh.scale.set(pulse.size, pulse.size, pulse.size);
      this.scene.add(mesh);
      this.plasmaPulses.push(pulse);
    }

    // Trigger explosive action potential cascade across the neural network
    triggerCascade(cascadeData) {
      if (!cascadeData) return;

      const seedId = String(cascadeData.seed || '');
      const seedMesh = this.nodeMeshes.get(seedId);

      // Bio-resonant audio feedback
      if (this.audio) this.audio.playActionPotential(528);

      // 1. Shockwave ring at origin seed
      if (seedMesh) {
        this.fireShockwave(seedMesh.position, 0xFFD700, 2.2);
        this.flashNode(seedMesh, 0xFFFFFF, 1.8);
      }

      // 2. Staggered sequence firing
      const sequence = cascadeData.cascade_sequence || [];
      sequence.forEach((step, index) => {
        const delayMs = index * 120; // 120ms transmission latency per hop
        setTimeout(() => {
          const srcId = String(step.source || '').replace('tag_', '').replace('mem_', '');
          const tgtId = String(step.target || '').replace('tag_', '').replace('mem_', '');

          const srcMesh = this.nodeMeshes.get(srcId) || this.findMeshByTag(srcId);
          const tgtMesh = this.nodeMeshes.get(tgtId) || this.findMeshByTag(tgtId);

          if (srcMesh && tgtMesh) {
            // High-speed plasma pulse firing
            const mid = new THREE.Vector3().addVectors(srcMesh.position, tgtMesh.position).multiplyScalar(0.5);
            mid.y += 20;
            const curve = new THREE.QuadraticBezierCurve3(srcMesh.position, mid, tgtMesh.position);

            this.spawnPlasmaPulse(curve, 0.9, 0xFFFFFF, 2.5);
            this.flashNode(tgtMesh, 0x00E5FF, 1.5);
          }
        }, delayMs);
      });

      this.stats.actionFrequency = Math.min(8.0, this.stats.actionFrequency + 0.6);
      this.updateHudStats();
    }

    findMeshByTag(tagClean) {
      const lower = tagClean.toLowerCase();
      for (const mesh of this.nodeMeshes.values()) {
        const tags = (mesh.userData.nodeData.tags || []).map(t => String(t).toLowerCase());
        if (tags.includes(lower)) return mesh;
      }
      return null;
    }

    // Concentric counter-rotating coronal shockwave rings
    fireShockwave(centerPos, color = 0xD4AF37, scaleRate = 1.8) {
      const ringGeo = new THREE.RingGeometry(2, 4.5, 36);
      const ringMat = new THREE.MeshBasicMaterial({
        color: color,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.9,
        blending: THREE.AdditiveBlending,
      });
      const ring = new THREE.Mesh(ringGeo, ringMat);
      ring.position.copy(centerPos);
      ring.rotation.x = Math.PI / 2;
      this.scene.add(ring);

      const ringGeo2 = new THREE.RingGeometry(1.5, 3, 28);
      const ringMat2 = new THREE.MeshBasicMaterial({
        color: 0xFFFFFF,
        side: THREE.DoubleSide,
        transparent: true,
        opacity: 0.7,
        blending: THREE.AdditiveBlending,
      });
      const ring2 = new THREE.Mesh(ringGeo2, ringMat2);
      ring2.position.copy(centerPos);
      ring2.rotation.x = Math.PI / 2;
      this.scene.add(ring2);

      let scale = 1.0;
      let opacity = 0.9;
      const expandInterval = setInterval(() => {
        scale += scaleRate;
        opacity -= 0.045;
        ring.scale.set(scale, scale, 1);
        ring2.scale.set(scale * 0.75, scale * 0.75, 1);
        ring.rotation.z += 0.05;
        ring2.rotation.z -= 0.05;
        ringMat.opacity = Math.max(0, opacity);
        ringMat2.opacity = Math.max(0, opacity * 0.75);

        if (opacity <= 0) {
          clearInterval(expandInterval);
          this.scene.remove(ring);
          this.scene.remove(ring2);
          ringGeo.dispose();
          ringMat.dispose();
          ringGeo2.dispose();
          ringMat2.dispose();
        }
      }, 16);
    }

    flashNode(mesh, flashColor = 0xFFFFFF, scaleMultiplier = 1.6) {
      if (!mesh || mesh.userData.isPulsing) return;
      mesh.userData.isPulsing = true;

      const baseRadius = mesh.userData.baseRadius;

      mesh.material.emissive.setHex(flashColor);
      mesh.material.emissiveIntensity = 2.2;
      mesh.scale.set(baseRadius * scaleMultiplier, baseRadius * scaleMultiplier, baseRadius * scaleMultiplier);

      setTimeout(() => {
        mesh.material.emissive.setHex(mesh.userData.baseColor);
        mesh.material.emissiveIntensity = 0.55;
        mesh.scale.set(baseRadius, baseRadius, baseRadius);
        mesh.userData.isPulsing = false;
      }, 450);
    }

    // Smoothly spotlights and glides camera to an engram node, highlighting its synaptic neighborhood
    focusNode(nodeId) {
      const mesh = this.nodeMeshes.get(String(nodeId));
      if (!mesh) return;

      this.selectedNode = mesh;
      this.flashNode(mesh, 0xFFD700, 2.0);
      this.fireShockwave(mesh.position, 0xFFD700, 2.0);
      if (this.audio) this.audio.playActionPotential(660);

      const targetPos = new THREE.Vector3(
        mesh.position.x + 35,
        mesh.position.y + 20,
        mesh.position.z + 65
      );
      this.glideCameraTo(targetPos, mesh.position);

      const connectedIds = new Set();
      this.filamentCurves.forEach(item => {
        if (item.sourceId === String(nodeId) || item.targetId === String(nodeId)) {
          connectedIds.add(item.sourceId === String(nodeId) ? item.targetId : item.sourceId);
          item.line.material.opacity = 1.0;
          item.line.material.color.setHex(0xFFD700);
          this.spawnPlasmaPulse(item.curve, 0.9, 0xFFFFFF, 3.0);
        } else {
          item.line.material.opacity = 0.12;
        }
      });

      connectedIds.forEach(id => {
        const neighbor = this.nodeMeshes.get(id);
        if (neighbor && !neighbor.userData.isPulsing) {
          neighbor.material.emissiveIntensity = 1.2;
        }
      });
    }

    clearHighlights() {
      this.filamentCurves.forEach(item => {
        const weight = item.weight || 0.2;
        if (weight >= 0.6) {
          item.line.material.opacity = 0.9;
          item.line.material.color.setHex(0xFFD700);
        } else if (weight >= 0.3) {
          item.line.material.opacity = 0.65;
          item.line.material.color.setHex(0x00E5FF);
        } else {
          item.line.material.opacity = 0.35;
          item.line.material.color.setHex(0x4A6CF7);
        }
      });

      this.nodeMeshes.forEach(mesh => {
        if (!mesh.userData.isPulsing) {
          mesh.material.emissiveIntensity = 0.55;
        }
      });
    }

    // Hippocampal Sleep Replay (Sharp-Wave Ripples & Consolidation Simulation)
    triggerSleepReplayCascade(report = {}) {
      if (this.audio) this.audio.playSleepRipple();

      // 1. Panoramic overview glide
      this.glideCameraTo(new THREE.Vector3(0, 220, 580), new THREE.Vector3(0, 0, 0));

      // 2. Sequential Hippocampal Sharp-Wave Ripples (SWRs) expanding radially from core
      const rippleColors = [0xFFD700, 0xA855F7, 0x00E5FF];
      rippleColors.forEach((col, idx) => {
        setTimeout(() => {
          this.fireShockwave(new THREE.Vector3(0, 0, 0), col, 3.2);
        }, idx * 260);
      });

      // 3. Stardust harmonic swirl
      if (this.stardustPoints && this.stardustPoints.material) {
        this.stardustPoints.material.opacity = 1.0;
        setTimeout(() => {
          this.stardustPoints.material.opacity = 0.75;
        }, 2800);
      }

      // 4. Wave of engram rehearsal & consolidation
      const allMeshes = Array.from(this.nodeMeshes.values());
      allMeshes.forEach((mesh, idx) => {
        const delay = 400 + (idx % 8) * 140;
        setTimeout(() => {
          this.flashNode(mesh, 0xFFD700, 1.8);
          this.filamentCurves.filter(f => f.sourceId === String(mesh.userData.nodeData.id)).forEach(f => {
            this.spawnPlasmaPulse(f.curve, 0.85, 0xFFD700, 2.2);
          });
        }, delay);
      });

      // 5. Pruning dissolution (if low-retention nodes exist)
      const prunedIds = report.pruned_ids || [];
      prunedIds.forEach(id => {
        const mesh = this.nodeMeshes.get(String(id));
        if (mesh) {
          this.dissolveNode(mesh);
        }
      });

      // 6. Display HUD sleep banner
      this.showSleepReplayBanner(report);
    }

    // Dissolve pruned memory engram into fading cosmic dust
    dissolveNode(mesh) {
      const pCount = 24;
      const geo = new THREE.BufferGeometry();
      const positions = new Float32Array(pCount * 3);
      const velocities = [];

      for (let i = 0; i < pCount; i++) {
        positions[i * 3] = mesh.position.x;
        positions[i * 3 + 1] = mesh.position.y;
        positions[i * 3 + 2] = mesh.position.z;
        velocities.push(new THREE.Vector3(
          (Math.random() - 0.5) * 1.8,
          (Math.random() - 0.5) * 1.8,
          (Math.random() - 0.5) * 1.8
        ));
      }
      geo.setAttribute('position', new THREE.BufferAttribute(positions, 3));
      const mat = new THREE.PointsMaterial({
        color: 0x9AA0A6,
        size: 2.5,
        transparent: true,
        opacity: 0.8,
      });
      const points = new THREE.Points(geo, mat);
      this.scene.add(points);

      let step = 0;
      const anim = setInterval(() => {
        step++;
        const pos = geo.attributes.position.array;
        for (let i = 0; i < pCount; i++) {
          pos[i * 3] += velocities[i].x;
          pos[i * 3 + 1] += velocities[i].y;
          pos[i * 3 + 2] += velocities[i].z;
        }
        geo.attributes.position.needsUpdate = true;
        mat.opacity -= 0.04;
        if (step >= 20 || mat.opacity <= 0) {
          clearInterval(anim);
          this.scene.remove(points);
          geo.dispose();
          mat.dispose();
        }
      }, 30);

      this.scene.remove(mesh);
      this.nodeMeshes.delete(String(mesh.userData.nodeData.id));
    }

    showSleepReplayBanner(report) {
      let banner = document.getElementById('nebula-sleep-banner');
      if (!banner) return;
      const reinforced = report.reinforced_synapses ?? report.rehearsed_count ?? report.reinforced ?? 8;
      const schemata = report.schemata_synthesized ?? 2;
      const pruned = report.pruned_count ?? 0;

      banner.innerHTML = `
        <div style="font-size:24px;">🌙</div>
        <div style="display:flex; flex-direction:column; gap:2px;">
          <div style="font-weight:700; font-size:12px; color:#FFD700; letter-spacing:0.5px;">HIPPOCAMPAL SLEEP REPLAY COMPLETE</div>
          <div style="font-size:11px; color:#EDEFF2;">Sharp-Wave Ripples (210 Hz) &bull; ${reinforced} Synapses Reinforced &bull; ${schemata} Schemata Synthesized &bull; ${pruned} Pruned</div>
        </div>
      `;
      banner.classList.add('visible');
      setTimeout(() => {
        banner.classList.remove('visible');
      }, 4800);
    }

    focusGalaxy(galaxyId) {
      if (galaxyId === 'core' || galaxyId === 'netrunner') {
        this.clearHighlights();
        this.fireShockwave(new THREE.Vector3(0, 0, 0), 0x00E5FF, 2.4);
        if (this.audio) this.audio.playActionPotential(640);
        this.glideCameraTo(new THREE.Vector3(0, 35, 145), new THREE.Vector3(0, -10, 0));
        return;
      }

      const galaxy = GALAXY_CLUSTERS[galaxyId];
      if (!galaxy) {
        // Reset to panoramic cosmic view
        this.clearHighlights();
        this.glideCameraTo(new THREE.Vector3(0, 180, 520), new THREE.Vector3(0, 0, 0));
        return;
      }

      this.clearHighlights();
      const targetPos = new THREE.Vector3(
        galaxy.center.x + 60,
        galaxy.center.y + 40,
        galaxy.center.z + 160
      );
      this.glideCameraTo(targetPos, galaxy.center);
    }

    glideCameraTo(endPos, endLook) {
      this.glideStartPos.copy(this.camera.position);
      this.glideEndPos.copy(endPos);
      this.glideStartLook.copy(this.controls ? this.controls.target : new THREE.Vector3());
      this.glideEndLook.copy(endLook);
      this.glideStartTime = this.clock.getElapsedTime();
      this.isGlidingCamera = true;
      if (this.controls) this.controls.autoRotate = false;
    }

    onWindowResize() {
      if (!this.container || !this.renderer || !this.camera) return;
      const width = this.container.clientWidth;
      const height = this.container.clientHeight;
      this.camera.aspect = width / height;
      this.camera.updateProjectionMatrix();
      this.renderer.setSize(width, height);
    }

    onMouseMove(event) {
      const rect = this.renderer.domElement.getBoundingClientRect();
      this.mouse.x = ((event.clientX - rect.left) / rect.width) * 2 - 1;
      this.mouse.y = -((event.clientY - rect.top) / rect.height) * 2 + 1;

      this.raycaster.setFromCamera(this.mouse, this.camera);
      const meshes = Array.from(this.nodeMeshes.values());
      if (this.netrunnerCore && this.netrunnerCore.innerCoreMesh) {
        meshes.push(this.netrunnerCore.innerCoreMesh);
      }
      const intersects = this.raycaster.intersectObjects(meshes);

      const tooltip = document.getElementById('nebula-hover-tooltip');

      if (intersects.length > 0) {
        const hitMesh = intersects[0].object;
        if (this.hoveredNode !== hitMesh) {
          if (this.hoveredNode && !this.hoveredNode.userData.isPulsing) {
            this.hoveredNode.material.emissiveIntensity = 0.55;
          }
          this.hoveredNode = hitMesh;
          this.hoveredNode.material.emissiveIntensity = 1.6;
          this.renderer.domElement.style.cursor = 'pointer';
        }

        if (tooltip) {
          const data = hitMesh.userData.nodeData;
          const galaxy = hitMesh.userData.galaxy;
          const label = data.text || data.label || 'Memory Engram';
          const cleanLabel = label.length > 55 ? label.slice(0, 52) + '...' : label;
          const access = data.access_count || 1;
          const imp = (typeof data.importance === 'number' ? data.importance : 1.0).toFixed(2);

          tooltip.innerHTML = `
            <div style="display:flex; align-items:center; justify-content:space-between; gap:8px; margin-bottom:4px;">
              <span style="font-weight:700; color:${galaxy.hex}; font-size:10px; text-transform:uppercase;">${galaxy.name}</span>
              <span style="font-size:10px; color:#9AA0A6;">Access: ${access}</span>
            </div>
            <div style="font-weight:500; font-size:12px; color:#EDEFF2; line-height:1.3; margin-bottom:4px;">${cleanLabel}</div>
            <div style="display:flex; align-items:center; justify-content:space-between; font-size:10px; color:#F5E6AB;">
              <span>Imp: ${imp}</span>
              <span style="color:#00E5FF; font-weight:600;">Click to inspect &rarr;</span>
            </div>
          `;

          const x = event.clientX - rect.left;
          const y = event.clientY - rect.top;
          tooltip.style.left = `${Math.min(x, rect.width - 240)}px`;
          tooltip.style.top = `${Math.max(20, y - 10)}px`;
          tooltip.classList.add('visible');
        }

        if (typeof this.onNodeHoverCallback === 'function') {
          this.onNodeHoverCallback(hitMesh.userData.nodeData, event);
        }
      } else {
        if (this.hoveredNode && !this.hoveredNode.userData.isPulsing) {
          this.hoveredNode.material.emissiveIntensity = 0.55;
        }
        this.hoveredNode = null;
        this.renderer.domElement.style.cursor = 'grab';

        if (tooltip) {
          tooltip.classList.remove('visible');
        }

        if (typeof this.onNodeHoverCallback === 'function') {
          this.onNodeHoverCallback(null, event);
        }
      }
    }

    handleNodeClick(event) {
      if (this.hoveredNode) {
        if (this.hoveredNode.userData && this.hoveredNode.userData.isNetrunnerCore) {
          this.focusGalaxy('core');
          this.triggerSleepReplayCascade({ reinforced_synapses: 12, schemata_synthesized: 3, pruned_count: 0 });
          if (typeof this.onNodeClickCallback === 'function') {
            this.onNodeClickCallback(this.hoveredNode.userData.nodeData);
          }
          return;
        }
        const nodeData = this.hoveredNode.userData.nodeData;
        this.focusNode(nodeData.id);

        if (typeof this.onNodeClickCallback === 'function') {
          this.onNodeClickCallback(nodeData);
        }
      } else {
        this.clearHighlights();
      }
    }

    connectSSE() {
      if (typeof EventSource === 'undefined') return;

      try {
        this.sseSource = new EventSource('/api/stream');
        this.sseSource.onmessage = (event) => {
          try {
            const parsed = JSON.parse(event.data);
            if (parsed.type === 'trigger') {
              this.triggerCascade(parsed.data.cascade);
            } else if (parsed.type === 'memory_created') {
              // Pulse Living Minds / Agents and refresh graph data
              if (window.fetchGraphData) window.fetchGraphData();
            } else if (parsed.type === 'neuromodulator_pulse') {
              // Color pulse across the nebula
              this.flashNebulaAura();
            }
          } catch (e) {
            // Ignore heartbeat pings
          }
        };

        this.sseSource.onerror = () => {
          // Reconnect automatically handled by EventSource
        };
      } catch (err) {
        console.warn('[NebulaEngine] SSE stream unavailable:', err);
      }
    }

    flashNebulaAura() {
      if (this.stardustPoints && this.stardustPoints.material) {
        this.stardustPoints.material.opacity = 1.0;
        setTimeout(() => {
          this.stardustPoints.material.opacity = 0.75;
        }, 500);
      }
    }

    updateHudStats() {
      const engramsEl = document.getElementById('hud-engrams-count');
      const synapsesEl = document.getElementById('hud-synapses-count');
      const freqEl = document.getElementById('hud-action-freq');

      if (engramsEl) engramsEl.innerText = this.stats.totalEngrams;
      if (synapsesEl) synapsesEl.innerText = this.stats.totalSynapses;
      if (freqEl) freqEl.innerText = `${this.stats.actionFrequency.toFixed(1)} Hz`;
    }

    animate() {
      requestAnimationFrame(() => this.animate());

      const delta = this.clock.getDelta();
      const time = this.clock.getElapsedTime();

      // 1. Controls update
      if (this.controls && !this.isGlidingCamera) {
        this.controls.update();
      }

      // 2. Smooth camera glide
      if (this.isGlidingCamera) {
        const elapsed = time - this.glideStartTime;
        const progress = Math.min(1.0, elapsed / 1.2); // 1.2s smooth glide
        const ease = 0.5 - Math.cos(progress * Math.PI) / 2; // smooth cosine ease

        this.camera.position.lerpVectors(this.glideStartPos, this.glideEndPos, ease);
        if (this.controls) {
          this.controls.target.lerpVectors(this.glideStartLook, this.glideEndLook, ease);
          this.controls.update();
        }

        if (progress >= 1.0) {
          this.isGlidingCamera = false;
        }
      }

      // 3. Stardust gentle harmonic oscillation
      if (this.stardustPositions && this.stardustPoints) {
        const positions = this.stardustPoints.geometry.attributes.position.array;
        for (let i = 0; i < positions.length; i += 3) {
          positions[i + 1] += Math.sin(time * 0.8 + positions[i] * 0.015) * 0.08;
        }
        this.stardustPoints.geometry.attributes.position.needsUpdate = true;
      }

      // 4. Galaxy Cores & Netrunner Cyber-Cortex rotation
      this.galaxyCores.forEach((c) => {
        if (c.ring) c.ring.rotation.z += 0.005;
      });
      if (this.netrunnerCore) {
        const nc = this.netrunnerCore;
        if (nc.brainWireMesh) {
          nc.brainWireMesh.rotation.y += 0.004;
          nc.brainWireMesh.rotation.x = Math.sin(time * 0.6) * 0.15;
        }
        if (nc.innerCoreMesh) {
          nc.innerCoreMesh.rotation.y -= 0.008;
          const pulseScale = 1.0 + Math.sin(time * 2.5) * 0.08;
          nc.innerCoreMesh.scale.set(pulseScale, pulseScale, pulseScale);
        }
        if (nc.gimbal1) {
          nc.gimbal1.rotation.z += 0.012;
          nc.gimbal1.rotation.x += 0.006;
        }
        if (nc.gimbal2) {
          nc.gimbal2.rotation.y -= 0.014;
          nc.gimbal2.rotation.z += 0.005;
        }
        if (nc.gimbal3) {
          nc.gimbal3.rotation.x += 0.01;
          nc.gimbal3.rotation.y += 0.008;
        }
      }

      // 5. Plasma Action Potential Pulses along Bezier Filaments
      for (let i = 0; i < this.plasmaPulses.length; i++) {
        const pulse = this.plasmaPulses[i];
        pulse.t += delta * pulse.speed;
        if (pulse.t >= 1.0) {
          pulse.t = 0.0;
        }
        const pos = pulse.curve.getPoint(pulse.t);
        pulse.mesh.position.copy(pos);
      }

      // 6. Action frequency decay toward resting baseline (1.2 Hz)
      if (this.stats.actionFrequency > 1.2) {
        this.stats.actionFrequency = Math.max(1.2, this.stats.actionFrequency - delta * 0.15);
        this.updateHudStats();
      }

      // 7. Render
      this.renderer.render(this.scene, this.camera);
    }
  }

  // Expose NebulaUniverse globally
  window.NebulaUniverse = NebulaUniverse;
})();
