// Forest Background Animation - Dark Green Theme (only on non-landing pages)
(function() {
  // Don't show canvas on landing page (it has the image background)
  if (window.location.pathname === '/' || window.location.pathname === '/index') {
    return;
  }
  
  const canvas = document.createElement('canvas');
  canvas.className = 'fixed inset-0 pointer-events-none z-0';
  canvas.style.opacity = '0.6';
  document.body.appendChild(canvas);

  const ctx = canvas.getContext('2d');
  if (!ctx) return;

  let animationFrameId;
  let time = 0;

  const resize = () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
  };

  resize();
  window.addEventListener('resize', resize);

  // Tree class for drawing tree silhouettes
  class Tree {
    constructor(x, baseHeight, width) {
      this.x = x;
      this.baseHeight = baseHeight;
      this.width = width;
      this.height = baseHeight + Math.random() * 20;
    }

    draw(context, canvasHeight) {
      const y = canvasHeight;
      const trunkHeight = this.height * 0.3;
      const crownHeight = this.height * 0.7;
      
      // Draw trunk
      context.fillStyle = 'rgba(60, 40, 20, 0.6)';
      context.fillRect(this.x - 8, y - trunkHeight, 16, trunkHeight);
      
      // Draw crown (foliage) - multiple layers for depth
      context.fillStyle = 'rgba(30, 50, 25, 0.5)';
      this.drawCrown(context, this.x, y - trunkHeight, crownHeight);
    }

    drawCrown(context, x, y, height) {
      // Draw multiple overlapping circles for tree crown
      const layers = 3;
      for (let i = 0; i < layers; i++) {
        const layerY = y - (height / layers) * i;
        const layerWidth = this.width * (1 - i * 0.2);
        const layerHeight = height / layers;
        
        context.beginPath();
        context.ellipse(x, layerY, layerWidth * 0.5, layerHeight * 0.6, 0, 0, Math.PI * 2);
        context.fill();
      }
    }
  }

  // Create trees
  const trees = [];
  function createTrees(canvasWidth, canvasHeight) {
    trees.length = 0;
    const treeCount = Math.floor(canvasWidth / 150);
    for (let i = 0; i < treeCount; i++) {
      const x = (canvasWidth / treeCount) * i + Math.random() * 50;
      const baseHeight = 80 + Math.random() * 60;
      const width = 40 + Math.random() * 30;
      trees.push(new Tree(x, baseHeight, width));
    }
  }

  // Particle system for morning mist
  class Particle {
    constructor(canvasWidth, canvasHeight) {
      this.canvasWidth = canvasWidth;
      this.canvasHeight = canvasHeight;
      this.x = Math.random() * this.canvasWidth;
      this.y = this.canvasHeight * 0.6 + Math.random() * (this.canvasHeight * 0.4);
      this.size = Math.random() * 80 + 40;
      this.speedX = Math.random() * 0.3 - 0.15;
      this.speedY = Math.random() * 0.1 - 0.05;
      this.opacity = Math.random() * 0.08 + 0.02;
    }

    update(canvasWidth, canvasHeight) {
      this.canvasWidth = canvasWidth;
      this.canvasHeight = canvasHeight;
      this.x += this.speedX;
      this.y += this.speedY;

      if (this.x > this.canvasWidth + this.size) this.x = -this.size;
      if (this.x < -this.size) this.x = this.canvasWidth + this.size;
      if (this.y > this.canvasHeight) this.y = this.canvasHeight * 0.6;
    }

    draw(context) {
      const gradient = context.createRadialGradient(this.x, this.y, 0, this.x, this.y, this.size);
      gradient.addColorStop(0, `rgba(150, 200, 150, ${this.opacity})`);
      gradient.addColorStop(1, 'rgba(150, 200, 150, 0)');
      context.fillStyle = gradient;
      context.fillRect(this.x - this.size, this.y - this.size, this.size * 2, this.size * 2);
    }
  }

  const particles = [];
  for (let i = 0; i < 20; i++) {
    particles.push(new Particle(canvas.width, canvas.height));
  }

  createTrees(canvas.width, canvas.height);

  const animate = () => {
    if (!ctx || !canvas) return;

    ctx.clearRect(0, 0, canvas.width, canvas.height);

    // Dark green forest gradient
    const forestGradient = ctx.createLinearGradient(0, 0, 0, canvas.height);
    forestGradient.addColorStop(0, 'rgba(20, 40, 25, 0.3)'); // Dark green top
    forestGradient.addColorStop(0.5, 'rgba(25, 50, 30, 0.25)'); // Medium green
    forestGradient.addColorStop(1, 'rgba(30, 60, 35, 0.2)'); // Lighter green bottom
    ctx.fillStyle = forestGradient;
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    // Subtle light rays through dark forest
    time += 0.001;
    for (let i = 0; i < 3; i++) {
      const sunX = (Math.sin(time * 0.3 + i * 2) * 0.2 + 0.5) * canvas.width;
      const rayGradient = ctx.createRadialGradient(
        sunX, 
        canvas.height * 0.1, 
        0, 
        sunX, 
        canvas.height * 0.8, 
        canvas.width * 0.3
      );
      rayGradient.addColorStop(0, 'rgba(100, 150, 100, 0.08)'); // Green-tinted light
      rayGradient.addColorStop(0.5, 'rgba(80, 120, 80, 0.04)');
      rayGradient.addColorStop(1, 'rgba(80, 120, 80, 0)');
      ctx.fillStyle = rayGradient;
      ctx.fillRect(0, 0, canvas.width, canvas.height);
    }

    // Draw trees
    trees.forEach((tree) => {
      tree.draw(ctx, canvas.height);
    });

    // Animate morning mist particles
    particles.forEach((particle) => {
      particle.update(canvas.width, canvas.height);
      particle.draw(ctx);
    });

    // Recreate trees if canvas resized
    if (trees.length === 0 || trees[0].x > canvas.width) {
      createTrees(canvas.width, canvas.height);
    }

    animationFrameId = requestAnimationFrame(animate);
  };

  animate();

  // Cleanup on page unload
  window.addEventListener('beforeunload', () => {
    window.removeEventListener('resize', resize);
    if (animationFrameId) {
      cancelAnimationFrame(animationFrameId);
    }
  });
})();
