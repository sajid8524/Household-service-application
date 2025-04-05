const Home = {
  template: `
    <div class="home">
      <!-- Welcome Section -->
      <div class="welcome-section">
        <h1>Welcome to Household Service Application</h1>
        <p>This is a platform for all your household services. From cleaning to repairs, we've got you covered!</p>
      </div>

      <!-- Centered Button -->
      <div class="button-container">
        <router-link to="/signup">
          <button class="cta-button">Get Started</button>
        </router-link>
      </div>

      <!-- Footer Section -->
      <footer>
        <p>Contact us: 8688057662 | support@houseservice.com</p>
      </footer>
    </div>
  `,
};

export default Home;