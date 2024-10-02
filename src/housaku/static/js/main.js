const CYCLES = 512;
const NUM_ELLIPSES = 64;
const FRAME_SPAN = CYCLES / NUM_ELLIPSES;
const ANGLES = [];
const RADII = [];
const PALETTE = [
  "#ff4800",
  "#ff5400",
  "#ff6000",
  "#ff6d00",
  "#ff7900",
  "#ff8500",
  "#ff9100",
  "#ff9e00",
  "#ffaa00",
  "#ffb600",
];

const getRatioEased = (count) => {
  const ratio = (count % CYCLES) / CYCLES;
  return easingEaseInOut(ratio) * 0.9 + ratio * 0.1;
};

const easingEaseInOut = (x) => {
  return x < 0.5 ? 0.5 * pow(2 * x, 3) : 0.5 * pow(2 * (x - 1), 3) + 1;
};

function setup() {
  frameRate(90);

  const canvas = createCanvas(windowWidth, windowHeight, WEBGL);
  canvas.id("animation");
  ortho(-width / 1.2, width / 1.2, -height / 1.2, height / 1.2);

  for (let i = 0; i < NUM_ELLIPSES; i++) {
    ANGLES[i] = (i / NUM_ELLIPSES) * TAU;
    RADII[i] = width * 0.3 * (0.6 + 0.4 * sin(ANGLES[i]));
  }
}

function draw() {
  const r = 0.5 * (width - width * 0.42);

  background(255, 0.0);
  noStroke();
  rotateX(-PI / 4);
  rotateY(-PI / 4);

  for (let i = 0; i < NUM_ELLIPSES; i++) {
    const angle = getRatioEased(frameCount + i * FRAME_SPAN) * TAU;
    const x = r * cos(angle);
    const z = r * sin(angle);

    fill(PALETTE[i % PALETTE.length]);
    push();
    translate(x, 0, z);
    rotateY(-angle);
    ellipse(0, 0, RADII[i], RADII[i], 50);
    pop();
  }
}
