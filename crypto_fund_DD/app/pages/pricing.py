import streamlit as st

# --- Pricing Plans Styling ---
pricing_style = """
<style>
:root {
    --primary: #3470fc;
    --secondary: #1847a8;
    --light: #f8f8f8;
    --dark: #011f3f;
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
    width: 0;
    height: 5px;
    background: var(--primary);
    bottom: 0;
    left: 50%;
    transform: translateX(-50%);
    border-radius: 2px;
    animation: growLine 1.5s ease forwards;
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

.pricing-item {
    background: rgba(255,255,255,0.05);
    backdrop-filter: blur(20px);
    border-radius: 20px;
    padding: 20px;
    text-align: center;
    box-shadow: 0 0 20px rgba(52, 112, 252, 0.4);
    transition: transform 0.3s ease;
}
.pricing-item:hover {
    transform: scale(1.05);
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
    color: #000000;
    font-size: 16px;
}
.pricing-btn {
    font-family: 'Nunito', sans-serif;
    font-weight: 600;
    padding: 10px 20px;
    border-radius: 30px;
    background: linear-gradient(90deg, #3470fc, #1847a8);
    color: #011f3f;
    border: none;
    transition: all 0.4s ease;
    text-decoration: none;
    display: inline-block;
}
.pricing-btn:hover {
    background: linear-gradient(90deg, #1847a8, #3470fc);
    transform: scale(1.05);
    box-shadow: 0 0 15px rgba(52, 112, 252, 0.5);
}
</style>
"""
st.markdown(pricing_style, unsafe_allow_html=True)

# --- Pricing Plans Section ---
st.markdown("""
<div style="padding: 50px 15px; background: var(--light);">
    <div class="section-title">
        <h5 class="fw-bold text-primary text-uppercase">Pricing Plans</h5>
        <h1 class="mb-0">Competitive Pricing for Crypto Due Diligence</h1>
    </div>
</div>
""", unsafe_allow_html=True)

col1, col2, col3 = st.columns(3)
with col1:
    st.markdown("""
    <div class="pricing-item">
        <div style="border-bottom: 1px solid #ddd; padding: 20px;">
            <h4 class="text-primary mb-1">Basic Plan</h4>
            <small class="text-uppercase">For Individual Investors</small>
        </div>
        <div style="padding: 20px;">
            <h1 class="mb-3" style="color: var(--dark);">
                <small style="font-size: 22px; vertical-align: top;">$</small>49.00
                <small style="font-size: 16px; vertical-align: bottom;">/ Month</small>
            </h1>
            <div class="feature"><span>Risk Scoring</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>Basic Analytics</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>Deep Search</span><i class="fa fa-times text-danger"></i></div>
            <div class="feature"><span>PPTX Reports</span><i class="fa fa-times text-danger"></i></div>
            <a href="#" class="pricing-btn py-2 px-4 mt-4">Order Now</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col2:
    st.markdown("""
    <div class="pricing-item" style="box-shadow: 0 0 30px rgba(52, 112, 252, 0.5); position: relative; z-index: 1;">
        <div style="border-bottom: 1px solid #ddd; padding: 20px;">
            <h4 class="text-primary mb-1">Standard Plan</h4>
            <small class="text-uppercase">For Small Funds</small>
        </div>
        <div style="padding: 20px;">
            <h1 class="mb-3" style="color: var(--dark);">
                <small style="font-size: 22px; vertical-align: top;">$</small>99.00
                <small style="font-size: 16px; vertical-align: bottom;">/ Month</small>
            </h1>
            <div class="feature"><span>Risk Scoring</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>Advanced Analytics</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>Deep Search</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>PPTX Reports</span><i class="fa fa-times text-danger"></i></div>
            <a href="#" class="pricing-btn py-2 px-4 mt-4">Order Now</a>
        </div>
    </div>
    """, unsafe_allow_html=True)
with col3:
    st.markdown("""
    <div class="pricing-item">
        <div style="border-bottom: 1px solid #ddd; padding: 20px;">
            <h4 class="text-primary mb-1">Advanced Plan</h4>
            <small class="text-uppercase">For Large Funds</small>
        </div>
        <div style="padding: 20px;">
            <h1 class="mb-3" style="color: var(--dark);">
                <small style="font-size: 22px; vertical-align: top;">$</small>149.00
                <small style="font-size: 16px; vertical-align: bottom;">/ Month</small>
            </h1>
            <div class="feature"><span>Risk Scoring</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>Advanced Analytics</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>Deep Search</span><i class="fa fa-check text-primary"></i></div>
            <div class="feature"><span>PPTX Reports</span><i class="fa fa-check text-primary"></i></div>
            <a href="#" class="pricing-btn py-2 px-4 mt-4">Order Now</a>
        </div>
    </div>
    """, unsafe_allow_html=True)

# Spacer
st.markdown('<div style="height: 50px;"></div>', unsafe_allow_html=True)