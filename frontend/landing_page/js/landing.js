const toggle = document.querySelector(".menu-toggle");
const navLinks = document.querySelector(".nav-links");

if (toggle && navLinks) {
  toggle.addEventListener("click", () => {
    const isOpen = navLinks.classList.toggle("is-open");
    toggle.setAttribute("aria-expanded", String(isOpen));
  });

  navLinks.addEventListener("click", (event) => {
    if (event.target instanceof HTMLAnchorElement) {
      navLinks.classList.remove("is-open");
      toggle.setAttribute("aria-expanded", "false");
    }
  });
}

const heroImages = document.querySelectorAll(".hero-image");
const heroLines = document.querySelectorAll(".hero-line");
const carouselDots = document.querySelectorAll(".carousel-dot");
let currentSlide = 0;
let carouselTimer;

function setActive(nodeList, index) {
  nodeList.forEach((node, i) => {
    node.classList.toggle("is-active", i === index);
  });
}

function showHeroSlide(slideIndex) {
  const total = heroImages.length;
  if (slideIndex < 0) {
    currentSlide = total - 1;
  } else if (slideIndex >= total) {
    currentSlide = 0;
  } else {
    currentSlide = slideIndex;
  }

  // image, headline text, and dot all move together
  setActive(heroImages, currentSlide);
  setActive(heroLines, currentSlide);
  setActive(carouselDots, currentSlide);

  // restart the progress animation on the active dot
  const activeDot = carouselDots[currentSlide];
  if (activeDot) {
    const activeProgress = activeDot.querySelector("span");
    if (activeProgress) {
      activeProgress.style.animation = "none";
      // force reflow so the animation restarts
      void activeProgress.offsetHeight;
      activeProgress.style.animation = "";
    }
  }
}

function startCarousel() {
  carouselTimer = setInterval(() => {
    showHeroSlide(currentSlide + 1);
  }, 5000);
}

function resetCarouselTimer() {
  clearInterval(carouselTimer);
  startCarousel();
}

if (heroImages.length > 1) {
  carouselDots.forEach((dot) => {
    dot.addEventListener("click", () => {
      const slideIndex = Number(dot.dataset.carouselSlide);
      showHeroSlide(slideIndex);
      resetCarouselTimer();
    });
  });

  startCarousel();
}