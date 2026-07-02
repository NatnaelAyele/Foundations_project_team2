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
const carouselDots = document.querySelectorAll(".carousel-dot");
let currentSlide = 0;
let carouselTimer;

function showHeroSlide(slideIndex) {
  if (slideIndex < 0) {
    currentSlide = heroImages.length - 1;
  } else if (slideIndex >= heroImages.length) {
    currentSlide = 0;
  } else {
    currentSlide = slideIndex;
  }

  heroImages.forEach((image, index) => {
    if (index === currentSlide) {
      image.classList.add("is-active");
    } else {
      image.classList.remove("is-active");
    }
  });

  carouselDots.forEach((dot, index) => {
    if (index === currentSlide) {
      dot.classList.add("is-active");
    } else {
      dot.classList.remove("is-active");
    }
  });

  const activeDot = carouselDots[currentSlide];

  if (activeDot) {
    const activeProgress = activeDot.querySelector("span");

    if (activeProgress) {
      activeProgress.style.animation = "none";
      activeProgress.offsetHeight;
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
