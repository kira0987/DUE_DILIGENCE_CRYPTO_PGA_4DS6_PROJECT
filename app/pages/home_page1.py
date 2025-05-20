import streamlit as st

# --- Set Page Config ---
st.set_page_config(
    page_title="Startup - Startup Website Template",
    page_icon="💼",
    layout="wide"
)

# --- Custom Styling ---
page_style = """
<style>
:root {
    --primary: #06A3DA;
    --secondary: #34AD54;
    --dark: #091E3E;
    --light: #F5F5F5;
}

[data-testid="stAppViewContainer"] {
    background: var(--light) !important;
    color: #333333;
    font-family: 'Nunito', sans-serif;
}

[data-testid="stHeader"] {
    background: transparent;
}

body {
    background: var(--light) !important;
    color: #333333;
    font-family: 'Nunito', sans-serif;
}

.text-primary {
    color: var(--primary) !important;
}

.text-white {
    color: #FFFFFF !important;
}

.text-dark {
    color: var(--dark) !important;
}

.text-uppercase {
    text-transform: uppercase !important;
}

.section-title {
    position: relative;
    padding-bottom: 10px;
    margin-bottom: 30px;
    text-align: center;
}
.section-title::before {
    content: "";
    position: absolute;
    width: 0; /* Start with 0 width */
    height: 5px;
    background: var(--primary);
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    border-radius: 2px;
    animation: growLine 1.5s ease forwards; /* Add animation */
}

@keyframes growLine {
    0% { width: 0; }
    100% { width: 150px; }
}
.section-title h5 {
    font-weight: 700;
    text-transform: uppercase;
    color: var(--primary);
    margin-bottom: 10px;
}
.section-title h1 {
    font-size: 36px;
    font-weight: 800;
    color: var(--dark);
    margin: 0;
}

.btn {
    font-family: 'Nunito', sans-serif;
    font-weight: 600;
    padding: 10px 20px;
    border-radius: 5px;
    transition: .5s;
}
.btn-primary {
    background-color: var(--primary);
    color: #FFFFFF;
    border: none;
}
.btn-primary:hover {
    background-color: #0579A1;
}
.btn-outline-light {
    color: #FFFFFF;
    border: 1px solid #FFFFFF;
    background: transparent;
}
.btn-outline-light:hover {
    color: var(--dark);
    background-color: #FFFFFF;
}

.carousel-caption {
    background: rgba(9, 30, 62, 0.7);
    padding: 40px;
    text-align: center;
    height: 500px;
    display: flex;
    align-items: center;
    justify-content: center;
}
.carousel-caption h5 {
    font-size: 18px;
    font-weight: 500;
    text-transform: uppercase;
    color: #FFFFFF;
    margin-bottom: 15px;
}
.carousel-caption h1 {
    font-size: 48px;
    font-weight: 600;
    color: #FFFFFF;
    margin-bottom: 20px;
}

.fact-item {
    background: #FFFFFF;
    padding: 20px;
    border-radius: 5px;
    text-align: center;
    display: flex;
    align-items: center;
    justify-content: center;
    height: 150px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}
.fact-item .icon {
    width: 60px;
    height: 60px;
    background: var(--primary);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 5px;
    margin-right: 15px;
}
.fact-item h5 {
    font-size: 18px;
    font-weight: 500;
    color: var(--dark);
    margin: 0;
}
.fact-item h1 {
    font-size: 36px;
    font-weight: 800;
    color: var(--dark);
    margin: 0;
}

.service-item {
    background: #FFFFFF;
    border-radius: 5px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}
.service-item:hover {
    box-shadow: 0 0 20px rgba(6, 163, 218, 0.3);
}
.service-icon {
    width: 60px;
    height: 60px;
    background: var(--primary);
    border-radius: 2px;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 20px;
}
.service-icon i {
    color: #FFFFFF;
    font-size: 24px;
}

.feature-item {
    display: flex;
    align-items: center;
    margin-bottom: 30px;
}
.feature-item .icon {
    width: 60px;
    height: 60px;
    background: var(--primary);
    display: flex;
    align-items: center;
    justify-content: center;
    border-radius: 5px;
    margin-right: 15px;
}
.feature-item h4 {
    font-size: 20px;
    font-weight: 600;
    color: var(--dark);
    margin: 0;
}
.feature-item p {
    font-size: 16px;
    color: #666666;
    margin: 5px 0 0;
}

.pricing-item {
    background: #FFFFFF;
    border-radius: 5px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.1);
}
.pricing-item h4 {
    font-size: 24px;
    font-weight: 600;
    color: var(--primary);
    margin: 0;
}
.pricing-item small {
    font-size: 14px;
    text-transform: uppercase;
    color: #666666;
}
.pricing-item h1 {
    font-size: 40px;
    font-weight: 700;
    color: var(--dark);
}
.pricing-item .feature {
    display: flex;
    justify-content: space-between;
    padding: 5px 0;
}
</style>
"""
st.markdown(page_style, unsafe_allow_html=True)

# --- Topbar ---
st.markdown("""
<div class="container-fluid px-5 d-none d-lg-block" style="height: 45px; background: var(--dark);">
    <div class="row gx-0" style="height: 100%;">
        <div class="col-lg-8 text-center text-lg-start">
            <div class="d-inline-flex align-items-center h-100">
                <small class="me-3 text-light"><i class="fa fa-map-marker-alt me-2"></i>123 Street, New York, USA</small>
                <small class="me-3 text-light"><i class="fa fa-phone-alt me-2"></i>+012 345 6789</small>
                <small class="text-light"><i class="fa fa-envelope-open me-2"></i>info@example.com</small>
            </div>
        </div>
        <div class="col-lg-4 text-center text-lg-end">
            <div class="d-inline-flex align-items-center h-100">
                <a class="btn btn-sm btn-outline-light btn-sm-square rounded-circle me-2" href="#" style="color: #FFFFFF; border-color: #FFFFFF;"><i class="fab fa-twitter fw-normal"></i></a>
                <a class="btn btn-sm btn-outline-light btn-sm-square rounded-circle me-2" href="#" style="color: #FFFFFF; border-color: #FFFFFF;"><i class="fab fa-facebook-f fw-normal"></i></a>
                <a class="btn btn-sm btn-outline-light btn-sm-square rounded-circle me-2" href="#" style="color: #FFFFFF; border-color: #FFFFFF;"><i class="fab fa-linkedin-in fw-normal"></i></a>
                <a class="btn btn-sm btn-outline-light btn-sm-square rounded-circle me-2" href="#" style="color: #FFFFFF; border-color: #FFFFFF;"><i class="fab fa-instagram fw-normal"></i></a>
                <a class="btn btn-sm btn-outline-light btn-sm-square rounded-circle" href="#" style="color: #FFFFFF; border-color: #FFFFFF;"><i class="fab fa-youtube fw-normal"></i></a>
            </div>
        </div>
    </div>
</div>
""", unsafe_allow_html=True)

# --- Navbar ---
st.markdown("""
<nav class="navbar navbar-expand-lg navbar-dark px-5 py-3 py-lg-0" style="background: var(--dark);">
    <div class="container-fluid">
        <a href="#" class="navbar-brand p-0">
            <h1 class="m-0 text-white"><i class="fa fa-user-tie me-2"></i>Startup</h1>
        </a>
        <div class="navbar-nav ms-auto py-0">
            <a href="#" class="nav-item nav-link active" style="color: #FFFFFF; padding: 10px 15px;">Home</a>
            <a href="#" class="nav-item nav-link" style="color: #FFFFFF; padding: 10px 15px;">About</a>
            <a href="#" class="nav-item nav-link" style="color: #FFFFFF; padding: 10px 15px;">Services</a>
            <div class="nav-item dropdown">
                <a href="#" class="nav-link dropdown-toggle" style="color: #FFFFFF; padding: 10px 15px;">Blog</a>
                <div class="dropdown-menu m-0" style="display: none; position: absolute; background: var(--dark); border: 1px solid var(--primary); border-radius: 5px;">
                    <a href="#" class="dropdown-item" style="color: #FFFFFF; padding: 10px;">Blog Grid</a>
                    <a href="#" class="dropdown-item" style="color: #FFFFFF; padding: 10px;">Blog Detail</a>
                </div>
            </div>
            <div class="nav-item dropdown">
                <a href="#" class="nav-link dropdown-toggle" style="color: #FFFFFF; padding: 10px 15px;">Pages</a>
                <div class="dropdown-menu m-0" style="display: none; position: absolute; background: var(--dark); border: 1px solid var(--primary); border-radius: 5px;">
                    <a href="#" class="dropdown-item" style="color: #FFFFFF; padding: 10px;">Pricing Plan</a>
                    <a href="#" class="dropdown-item" style="color: #FFFFFF; padding: 10px;">Our features</a>
                    <a href="#" class="dropdown-item" style="color: #FFFFFF; padding: 10px;">Team Members</a>
                    <a href="#" class="dropdown-item" style="color: #FFFFFF; padding: 10px;">Testimonial</a>
                    <a href="#" class="dropdown-item" style="color: #FFFFFF; padding: 10px;">Free Quote</a>
                </div>
            </div>
            <a href="#" class="nav-item nav-link" style="color: #FFFFFF; padding: 10px 15px;">Contact</a>
        </div>
        <a href="#" class="btn btn-primary py-2 px-4 ms-3">Download Pro Version</a>
    </div>
</nav>
""", unsafe_allow_html=True)

# --- Carousel (Static with Images) ---
with open("assets/img/carousel-1.jpg", "rb") as f:
    st.image(f.read(), use_column_width=True, caption="Creative & Innovative Digital Solution")
st.markdown("""
<div class="carousel-caption" style="height: 500px; display: flex; align-items: center; justify-content: center; background: rgba(9, 30, 62, 0.7);">
    <div style="max-width: 900px; text-align: center;">
        <h5 class="text-white text-uppercase mb-3">Creative & Innovative</h5>
        <h1 class="display-1 text-white mb-4">Creative & Innovative Digital Solution</h1>
        <a href="#" class="btn btn-primary py-md-3 px-md-5 me-3">Free Quote</a>
        <a href="#" class="btn btn-outline-light py-md-3 px-md-5">Contact Us</a>
    </div>
</div>
""", unsafe_allow_html=True)
st.markdown("**Note**: The carousel slideshow animation is not supported in Streamlit. This is a static version with the first image.", unsafe_allow_html=False)

# --- Facts ---
st.markdown('<div style="padding: 50px 15px; background: var(--light);">', unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="fact-item">
        <div class="icon"><i class="fa fa-users text-white"></i></div>
        <div>
            <h5 class="text-dark mb-0">Happy Clients</h5>
            <h1 class="text-dark mb-0">12345</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="fact-item">
        <div class="icon"><i class="fa fa-check text-white"></i></div>
        <div>
            <h5 class="text-dark mb-0">Projects Done</h5>
            <h1 class="text-dark mb-0">12345</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="fact-item">
        <div class="icon"><i class="fa fa-award text-white"></i></div>
        <div>
            <h5 class="text-dark mb-0">Win Awards</h5>
            <h1 class="text-dark mb-0">12345</h1>
        </div>
    </div>
    """, unsafe_allow_html=True)
st.markdown("**Note**: The counter-up animation for numbers is not supported in Streamlit. These are static values.", unsafe_allow_html=False)
st.markdown('</div>', unsafe_allow_html=True)

# --- About ---
st.markdown("""
<div style="padding: 50px 15px; background: var(--light);">
    <div class="section-title">
        <h5 class="fw-bold text-primary text-uppercase">About Us</h5>
        <h1 class="mb-0">Your Trusted Partner in Crypto Due Diligence</h1>
    </div>
</div>
""", unsafe_allow_html=True)
col1, col2 = st.columns([2, 1])
with col1:
    st.markdown("""
    <p style="margin-bottom: 20px; color: #666666;">DueXpert leverages AI to deliver cutting-edge due diligence for crypto investments, helping you navigate risks and make informed decisions with confidence.</p>
    <div style="display: flex; flex-wrap: wrap; gap: 20px; margin-bottom: 20px;">
        <div style="flex: 1; min-width: 200px;">
            <h5 style="margin-bottom: 10px; color: #333333;"><i class="fa fa-check text-primary me-3"></i>Risk Mitigation</h5>
            <h5 style="margin-bottom: 10px; color: #333333;"><i class="fa fa-check text-primary me-3"></i>AI-Driven Insights</h5>
        </div>
        <div style="flex: 1; min-width: 200px;">
            <h5 style="margin-bottom: 10px; color: #333333;"><i class="fa fa-check text-primary me-3"></i>24/7 Support</h5>
            <h5 style="margin-bottom: 10px; color: #333333;"><i class="fa fa-check text-primary me-3"></i>Transparent Analysis</h5>
        </div>
    </div>
    <div style="display: flex; align-items: center; margin-bottom: 20px;">
        <div class="icon" style="width: 60px; height: 60px; background: var(--primary); display: flex; align-items: center; justify-content: center; border-radius: 5px; margin-right: 15px;">
            <i class="fa fa-phone-alt text-white"></i>
        </div>
        <div>
            <h5 style="margin: 0; color: #333333;">Need Assistance?</h5>
            <h4 style="color: var(--primary); margin: 0;">+012 345 6789</h4>
        </div>
    </div>
    <a href="#" class="btn btn-primary py-3 px-5">Get Started Now</a>
    """, unsafe_allow_html=True)
with col2:
    with open("assets/img/crypto.jpeg", "rb") as f:
        st.image(f.read(), use_column_width=True)
        
# --- Features ---
st.markdown("""
<div style="padding: 50px 15px; background: var(--light);">
    <div class="section-title">
        <h5 class="fw-bold text-primary text-uppercase">Why Choose Us</h5>
        <h1 class="mb-0">We Are Here to Grow Your Business Exponentially</h1>
    </div>
</div>
""", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="feature-item">
        <div class="icon"><i class="fa fa-cubes text-white"></i></div>
        <div>
            <h4>Best In Industry</h4>
            <p class="mb-0">Magna sea eos sit dolor, ipsum amet lorem diam dolor eos et diam dolor</p>
        </div>
    </div>
    <div class="feature-item">
        <div class="icon"><i class="fa fa-award text-white"></i></div>
        <div>
            <h4>Award Winning</h4>
            <p class="mb-0">Magna sea eos sit dolor, ipsum amet lorem diam dolor eos et diam dolor</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    with open("assets/img/feature.jpg", "rb") as f:
        st.image(f.read(), use_column_width=True)
with col3:
    st.markdown("""
    <div class="feature-item">
        <div class="icon"><i class="fa fa-users-cog text-white"></i></div>
        <div>
            <h4>Professional Staff</h4>
            <p class="mb-0">Magna sea eos sit dolor, ipsum amet lorem diam dolor eos et diam dolor</p>
        </div>
    </div>
    <div class="feature-item">
        <div class="icon"><i class="fa fa-phone-alt text-white"></i></div>
        <div>
            <h4>24/7 Support</h4>
            <p class="mb-0">Magna sea eos sit dolor, ipsum amet lorem diam dolor eos et diam dolor</p>
        </div>
    </div>
    """, unsafe_allow_html=True)
st.markdown("**Note**: The zoom-in animations for feature items are not supported in Streamlit. This is a static version.", unsafe_allow_html=False)

# --- Services ---
st.markdown("""
<div style="padding: 50px 15px; background: var(--light);">
    <div class="section-title">
        <h5 class="fw-bold text-primary text-uppercase">Our Services</h5>
        <h1 class="mb-0">Custom IT Solutions for Your Successful Business</h1>
    </div>
</div>
""", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="service-item">
        <div class="service-icon"><i class="fa fa-shield-alt text-white"></i></div>
        <h4 class="mb-3">Cyber Security</h4>
        <p class="m-0">Amet justo dolor lorem kasd amet magna sea stet eos vero lorem ipsum dolore sed</p>
        <a class="btn btn-lg btn-primary rounded mt-3" href="#"><i class="bi bi-arrow-right"></i></a>
    </div>
    <div class="service-item" style="margin-top: 20px;">
        <div class="service-icon"><i class="fab fa-android text-white"></i></div>
        <h4 class="mb-3">Apps Development</h4>
        <p class="m-0">Amet justo dolor lorem kasd amet magna sea stet eos vero lorem ipsum dolore sed</p>
        <a class="btn btn-lg btn-primary rounded mt-3" href="#"><i class="bi bi-arrow-right"></i></a>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="service-item">
        <div class="service-icon"><i class="fa fa-chart-pie text-white"></i></div>
        <h4 class="mb-3">Data Analytics</h4>
        <p class="m-0">Amet justo dolor lorem kasd amet magna sea stet eos vero lorem ipsum dolore sed</p>
        <a class="btn btn-lg btn-primary rounded mt-3" href="#"><i class="bi bi-arrow-right"></i></a>
    </div>
    <div class="service-item" style="margin-top: 20px;">
        <div class="service-icon"><i class="fa fa-search text-white"></i></div>
        <h4 class="mb-3">SEO Optimization</h4>
        <p class="m-0">Amet justo dolor lorem kasd amet magna sea stet eos vero lorem ipsum dolore sed</p>
        <a class="btn btn-lg btn-primary rounded mt-3" href="#"><i class="bi bi-arrow-right"></i></a>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="service-item">
        <div class="service-icon"><i class="fa fa-code text-white"></i></div>
        <h4 class="mb-3">Web Development</h4>
        <p class="m-0">Amet justo dolor lorem kasd amet magna sea stet eos vero lorem ipsum dolore sed</p>
        <a class="btn btn-lg btn-primary rounded mt-3" href="#"><i class="bi bi-arrow-right"></i></a>
    </div>
    <div class="service-item bg-primary rounded d-flex flex-column align-items-center justify-content-center text-center p-5" style="margin-top: 20px; height: 300px;">
        <h3 class="text-white mb-3">Call Us For Quote</h3>
        <p class="text-white mb-3">Clita ipsum magna kasd rebum at ipsum amet dolor justo dolor est magna stet eirmod</p>
        <h2 class="text-white mb-0">+012 345 6789</h2>
    </div>
    """, unsafe_allow_html=True)

# --- Pricing ---
st.markdown("""
<div style="padding: 50px 15px; background: var(--light);">
    <div class="section-title">
        <h5 class="fw-bold text-primary text-uppercase">Pricing Plans</h5>
        <h1 class="mb-0">We are Offering Competitive Prices for Our Clients</h1>
    </div>
</div>
""", unsafe_allow_html=True)
col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="pricing-item">
        <div style="border-bottom: 1px solid #ddd; padding: 20px;">
            <h4 class="text-primary mb-1">Basic Plan</h4>
            <small class="text-uppercase">For Small Size Business</small>
        </div>
        <div style="padding: 20px;">
            <h1 class="mb-3" style="color: var(--dark);">
                <small style="font-size: 22px; vertical-align: top;">$</small>49.00
                <small style="font-size: 16px; vertical-align: bottom;">/ Month</small>
            </h1>
            <div class="feature"><span style="color: #666666;">HTML5 & CSS3</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span style="color: #666666;">Bootstrap v5</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span style="color: #666666;">Responsive Layout</span><i class="fa fa-times text-danger"></i></div>
            <div class="feature"><span style="color: #666666;">Cross-browser Support</span><i class="fa fa-times text-danger"></i></div>
            <a href="#" class="btn btn-primary py-2 px-4 mt-4">Order Now</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="pricing-item" style="box-shadow: 0 0 20px rgba(0, 0, 0, 0.2); position: relative; z-index: 1;">
        <div style="border-bottom: 1px solid #ddd; padding: 20px;">
            <h4 class="text-primary mb-1">Standard Plan</h4>
            <small class="text-uppercase">For Medium Size Business</small>
        </div>
        <div style="padding: 20px;">
            <h1 class="mb-3" style="color: var(--dark);">
                <small style="font-size: 22px; vertical-align: top;">$</small>99.00
                <small style="font-size: 16px; vertical-align: bottom;">/ Month</small>
            </h1>
            <div class="feature"><span style="color: #666666;">HTML5 & CSS3</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span style="color: #666666;">Bootstrap v5</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span style="color: #666666;">Responsive Layout</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span style="color: #666666;">Cross-browser Support</span><i class="fa fa-times text-danger"></i></div>
            <a href="#" class="btn btn-primary py-2 px-4 mt-4">Order Now</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="pricing-item">
        <div style="border-bottom: 1px solid #ddd; padding: 20px;">
            <h4 class="text-primary mb-1">Advanced Plan</h4>
            <small class="text-uppercase">For Large Size Business</small>
        </div>
        <div style="padding: 20px;">
            <h1 class="mb-3" style="color: var(--dark);">
                <small style="font-size: 22px; vertical-align: top;">$</small>149.00
                <small style="font-size: 16px; vertical-align: bottom;">/ Month</small>
            </h1>
            <div class="feature"><span style="color: #666666;">HTML5 & CSS3</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span style="color: #666666;">Bootstrap v5</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span style="color: #666666;">Responsive Layout</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span style="color: #666666;">Cross-browser Support</span><i class="fa fa-check text-primary"></i></div>
            <a href="#" class="btn btn-primary py-2 px-4 mt-4">Order Now</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# --- Footer ---
st.markdown("""
<div class="container-fluid text-light mt-5" style="padding: 50px 15px; background: var(--dark);">
    <div class="row">
        <div class="col-lg-4 col-md-6">
            <div style="background: var(--primary); padding: 30px; text-align: center; border-radius: 5px;">
                <h1 class="m-0 text-white"><i class="fa fa-user-tie me-2"></i>Startup</h1>
                <p class="mt-3 mb-4">Lorem diam sit erat dolor elitr et, diam lorem justo amet clita stet eos sit. Elitr dolor duo lorem, elitr clita ipsum sea. Diam amet erat lorem stet eos. Diam amet et kasd eos duo.</p>
                <div style="display: flex; gap: 10px; justify-content: center;">
                    <input type="text" placeholder="Your Email" style="padding: 10px; border-radius: 5px; border: 1px solid #fff; background: transparent; color: #fff;">
                    <button class="btn btn-dark" style="background: #333;">Sign Up</button>
                </div>
            </div>
        </div>
        <div class="col-lg-8 col-md-6">
            <div class="row">
                <div class="col-lg-4 col-md-12 pt-5 pt-lg-0">
                    <h3 class="text-light mb-4">Get In Touch</h3>
                    <p class="mb-2"><i class="bi bi-geo-alt text-primary me-2"></i>123 Street, New York, USA</p>
                    <p class="mb-2"><i class="bi bi-envelope-open text-primary me-2"></i>info@example.com</p>
                    <p class="mb-2"><i class="bi bi-telephone text-primary me-2"></i>+012 345 67890</p>
                    <div class="d-flex mt-4">
                        <a class="btn btn-primary btn-square me-2" href="#" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;"><i class="fab fa-twitter fw-normal"></i></a>
                        <a class="btn btn-primary btn-square me-2" href="#" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;"><i class="fab fa-facebook-f fw-normal"></i></a>
                        <a class="btn btn-primary btn-square me-2" href="#" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;"><i class="fab fa-linkedin-in fw-normal"></i></a>
                        <a class="btn btn-primary btn-square" href="#" style="width: 40px; height: 40px; display: flex; align-items: center; justify-content: center;"><i class="fab fa-instagram fw-normal"></i></a>
                    </div>
                </div>
                <div class="col-lg-4 col-md-12 pt-5 pt-lg-0">
                    <h3 class="text-light mb-4">Quick Links</h3>
                    <a class="text-light mb-2 d-block" href="#" style="color: #FFFFFF;"><i class="bi bi-arrow-right text-primary me-2"></i>Home</a>
                    <a class="text-light mb-2 d-block" href="#" style="color: #FFFFFF;"><i class="bi bi-arrow-right text-primary me-2"></i>About Us</a>
                    <a class="text-light mb-2 d-block" href="#" style="color: #FFFFFF;"><i class="bi bi-arrow-right text-primary me-2"></i>Our Services</a>
                    <a class="text-light mb-2 d-block" href="#" style="color: #FFFFFF;"><i class="bi bi-arrow-right text-primary me-2"></i>Meet The Team</a>
                    <a class="text-light mb-2 d-block" href="#" style="color: #FFFFFF;"><i class="bi bi-arrow-right text-primary me-2"></i>Latest Blog</a>
                    <a class="text-light d-block" href="#" style="color: #FFFFFF;"><i class="bi bi-arrow-right text-primary me-2"></i>Contact Us</a>
                </div>
                <div class="col-lg-4 col-md-12 pt-5 pt-lg-0">
                    <h3 class="text-light mb-4">Popular Links</h3>
                    <a class="text-light mb-2 d-block" href="#" style="color: #FFFFFF;"><i class="bi bi-arrow-right text-primary me-2"></i>Home</a>
                    <a class="text-light mb-2 d-block" href="#" style="color: #FFFFFF;"><i class="bi bi-arrow-right text-primary me-2"></i>About Us</a>
                    <a class="text-light mb-2 d-block" href="#" style="color: #FFFFFF;"><i class="bi bi-arrow-right text-primary me-2"></i>Our Services</a>
                    <a class="text-light mb-2 d-block" href="#" style="color: #FFFFFF;"><i class="bi bi-arrow-right text-primary me-2"></i>Meet The Team</a>
                    <a class="text-light mb-2 d-block" href="#" style="color: #FFFFFF;"><i class="bi bi-arrow-right text-primary me-2"></i>Latest Blog</a>
                    <a class="text-light d-block" href="#" style="color: #FFFFFF;"><i class="bi bi-arrow-right text-primary me-2"></i>Contact Us</a>
                </div>
            </div>
        </div>
    </div>
</div>
<div style="background: #061429; padding: 20px; text-align: center; color: #FFFFFF;">
    <p class="mb-0">© <a class="text-white border-bottom" href="#" style="color: #FFFFFF; text-decoration: none; border-bottom: 1px solid #FFFFFF;">Your Site Name</a>. All Rights Reserved. Designed by <a class="text-white border-bottom" href="https://htmlcodex.com" style="color: #FFFFFF; text-decoration: none; border-bottom: 1px solid #FFFFFF;">HTML Codex</a></p>
</div>
""", unsafe_allow_html=True)