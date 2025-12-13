// Game Configuration
const config = {
    width: 800,
    height: 600,
    fps: 60,
    gravity: 1.0,
    jumpStrength: -20,
    speed: 7,
    playerRunTilt: 5,
    bridgeWidth: 120,
    bridgeHeight: 40,
    bridgeY: 460
};

// Game State
let gameState = {
    running: false,
    gameOver: false,
    score: 0,
    player: null,
    bridges: [],
    assetsLoaded: false
};

// Assets
const assets = {
    player: null,
    bridge: null,
    fire: null,
    background: null,
    gameOverImage: null,
    screamSound: null,
    backgroundMusic: null
};

// Canvas Setup
const canvas = document.getElementById('gameCanvas');
const ctx = canvas.getContext('2d');

// UI Elements
const startScreen = document.getElementById('startScreen');
const gameOverScreen = document.getElementById('gameOverScreen');
const loadingScreen = document.getElementById('loadingScreen');
const startBtn = document.getElementById('startBtn');
const restartBtn = document.getElementById('restartBtn');
const scoreValue = document.getElementById('scoreValue');
const finalScore = document.getElementById('finalScore');

// Player Class
class Player {
    constructor() {
        this.width = 80;
        this.height = 80;
        this.x = 150;
        this.y = 300;
        this.velocityY = 0;
        this.jumping = false;
        this.onGround = false;
        this.animationTimer = 0;
        this.tilt = 0;
    }

    update(bridges) {
        // Apply gravity
        this.velocityY += config.gravity;

        // Terminal velocity
        if (this.velocityY > 25) {
            this.velocityY = 25;
        }

        this.y += this.velocityY;

        // Animation
        this.animationTimer++;

        // Update tilt based on state
        if (this.onGround && !this.jumping) {
            this.tilt = config.playerRunTilt + 2 * (this.animationTimer % 10) / 10;
        } else if (this.jumping && this.velocityY < 0) {
            this.tilt = -10;
        } else {
            this.tilt = Math.min(15, Math.abs(this.velocityY) * 0.8);
        }

        // Collision detection
        this.onGround = false;
        for (let bridge of bridges) {
            if (this.velocityY > 0) {
                if (this.x + this.width > bridge.x &&
                    this.x < bridge.x + bridge.width &&
                    this.y + this.height >= bridge.y &&
                    this.y < bridge.y) {
                    this.y = bridge.y - this.height;
                    this.velocityY = 0;
                    this.jumping = false;
                    this.onGround = true;
                    break;
                }
            }
        }
    }

    jump() {
        if (this.onGround) {
            this.velocityY = config.jumpStrength;
            this.jumping = true;
            this.onGround = false;
        }
    }

    draw() {
        ctx.save();
        ctx.translate(this.x + this.width / 2, this.y + this.height / 2);
        ctx.rotate((this.tilt * Math.PI) / 180);

        if (assets.player) {
            ctx.drawImage(
                assets.player,
                -this.width / 2,
                -this.height / 2,
                this.width,
                this.height
            );
        } else {
            ctx.fillStyle = '#fff';
            ctx.fillRect(-this.width / 2, -this.height / 2, this.width, this.height);
        }

        ctx.restore();
    }
}

// Bridge Class
class Bridge {
    constructor(x, y) {
        this.x = x;
        this.y = y;
        this.width = config.bridgeWidth;
        this.height = config.bridgeHeight;
    }

    update() {
        this.x -= config.speed;
    }

    draw() {
        if (assets.bridge) {
            ctx.drawImage(assets.bridge, this.x, this.y, this.width, this.height);
        } else {
            ctx.fillStyle = '#8B5A2B';
            ctx.fillRect(this.x, this.y, this.width, this.height);
        }
    }
}

// Load Assets
async function loadAssets() {
    const loadImage = (src) => {
        return new Promise((resolve, reject) => {
            const img = new Image();
            img.onload = () => resolve(img);
            img.onerror = () => resolve(null);
            img.src = src;
        });
    };

    const loadAudio = (src) => {
        return new Promise((resolve) => {
            const audio = new Audio();
            audio.oncanplaythrough = () => resolve(audio);
            audio.onerror = () => resolve(null);
            audio.src = src;
        });
    };

    try {
        // Load images
        assets.player = await loadImage('player.png');
        assets.bridge = await loadImage('bridge.png');
        assets.fire = await loadImage('fire.png');
        assets.background = await loadImage('background.png');
        assets.gameOverImage = await loadImage('amit.jpg');

        // Load audio
        assets.screamSound = await loadAudio('Game over sound.mp3');
        assets.backgroundMusic = await loadAudio('background_music.mp3');

        if (assets.backgroundMusic) {
            assets.backgroundMusic.loop = true;
            assets.backgroundMusic.volume = 0.3;
        }

        if (assets.screamSound) {
            assets.screamSound.volume = 0.7;
        }

        // Set game over image
        const gameOverImg = document.getElementById('gameOverImage');
        if (assets.gameOverImage) {
            gameOverImg.src = 'amit.jpg';
        }

        assets.assetsLoaded = true;
        console.log('Assets loaded successfully!');
    } catch (error) {
        console.error('Error loading assets:', error);
        assets.assetsLoaded = true; // Continue anyway
    }
}

// Initialize Game
function initGame() {
    gameState.score = 0;
    gameState.gameOver = false;
    gameState.running = true;
    gameState.player = new Player();
    gameState.bridges = [];

    // Create initial bridges
    for (let i = 0; i < 10; i++) {
        const bridge = new Bridge(i * config.bridgeWidth, config.bridgeY);
        gameState.bridges.push(bridge);
    }

    // Play background music
    if (assets.backgroundMusic) {
        assets.backgroundMusic.play().catch(e => console.log('Audio play failed:', e));
    }
}

// Update Game
function update() {
    if (!gameState.running || gameState.gameOver) return;

    gameState.score++;

    // Spawn new bridges
    if (gameState.bridges.length > 0) {
        const rightmost = gameState.bridges.reduce((max, b) =>
            b.x + b.width > max ? b.x + b.width : max, 0);

        if (rightmost < config.width + 200) {
            let newX;
            // Add gaps after score > 150
            if (Math.random() < 0.25 && gameState.score > 150) {
                const gapSize = Math.floor(Math.random() * (220 - 130 + 1)) + 130;
                newX = rightmost + gapSize;
            } else {
                const smallGap = gameState.score > 100 ? Math.floor(Math.random() * 16) : 0;
                newX = rightmost + smallGap;
            }
            const bridge = new Bridge(newX, config.bridgeY);
            gameState.bridges.push(bridge);
        }
    }

    // Update player
    gameState.player.update(gameState.bridges);

    // Update bridges
    gameState.bridges = gameState.bridges.filter(bridge => {
        bridge.update();
        return bridge.x + bridge.width > 0;
    });

    // Check game over
    if (gameState.player.y > config.height) {
        gameState.gameOver = true;
        gameState.running = false;

        // Play scream sound
        if (assets.screamSound) {
            assets.screamSound.play().catch(e => console.log('Audio play failed:', e));
        }

        // Stop background music
        if (assets.backgroundMusic) {
            assets.backgroundMusic.pause();
            assets.backgroundMusic.currentTime = 0;
        }

        // Show game over screen
        showGameOver();
    }
}

// Draw Game
function draw() {
    // Clear canvas
    ctx.clearRect(0, 0, config.width, config.height);

    // Draw background
    if (assets.background) {
        ctx.drawImage(assets.background, 0, 0, config.width, config.height);
    } else {
        ctx.fillStyle = '#141428';
        ctx.fillRect(0, 0, config.width, config.height);
    }

    // Draw bridges
    gameState.bridges.forEach(bridge => bridge.draw());

    // Draw player
    if (gameState.player) {
        gameState.player.draw();
    }

    // Draw fire
    if (assets.fire) {
        ctx.drawImage(assets.fire, 0, config.height - 100, config.width, 150);
    } else {
        ctx.fillStyle = '#ff0000';
        ctx.fillRect(0, config.height - 50, config.width, 50);
    }

    // Update score display
    scoreValue.textContent = `${Math.floor(gameState.score / 10)}m`;
}

// Game Loop
function gameLoop() {
    update();
    draw();
    requestAnimationFrame(gameLoop);
}

// Show Game Over
function showGameOver() {
    finalScore.textContent = `${Math.floor(gameState.score / 10)}m`;
    gameOverScreen.classList.add('active');
}

// Event Listeners
startBtn.addEventListener('click', () => {
    startScreen.classList.add('hidden');
    initGame();
    gameLoop();
});

restartBtn.addEventListener('click', () => {
    gameOverScreen.classList.remove('active');
    initGame();
});

// Keyboard Controls
document.addEventListener('keydown', (e) => {
    if (e.code === 'Space') {
        e.preventDefault();
        if (!gameState.running && !gameState.gameOver && !startScreen.classList.contains('hidden')) {
            // Start game from start screen
            startScreen.classList.add('hidden');
            initGame();
            gameLoop();
        } else if (gameState.running && !gameState.gameOver) {
            // Jump during game
            gameState.player.jump();
        } else if (gameState.gameOver) {
            // Restart from game over
            gameOverScreen.classList.remove('active');
            initGame();
        }
    }
});

// Load assets on page load
window.addEventListener('load', async () => {
    await loadAssets();
    loadingScreen.classList.add('hidden');
});

// Start initial draw
draw();
