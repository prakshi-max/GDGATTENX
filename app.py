import json
import os
import warnings
import streamlit as st

# Suppress Firestore warnings
warnings.filterwarnings("ignore", message="Detected filter using positional arguments")

# Google OAuth2 setup
CLIENT_ID = st.secrets["google_oauth"]["client_id"]
CLIENT_SECRET = st.secrets["google_oauth"]["client_secret"]
REDIRECT_URI = 'https://gdgattenx-ndtstcldaclx7pffkpymgp.streamlit.app/'
SCOPE = 'openid email profile'

from dotenv import load_dotenv
load_dotenv('config.env')
from firebase_admin_init import db
from datetime import datetime
import cv2
import numpy as np
from PIL import Image
from collections import Counter
from streamlit_oauth import OAuth2Component
import qrcode
import io
import base64

# List of admin emails
ADMIN_EMAILS = [
    'prakshigoel59@gmail.com',  # Add your admin emails here
    # 'anotheradmin@example.com',
]

oauth2 = OAuth2Component(
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
    authorize_endpoint="https://accounts.google.com/o/oauth2/v2/auth",
    token_endpoint="https://oauth2.googleapis.com/token"
)

if 'user_email' not in st.session_state:
    st.session_state['user_email'] = None

st.set_page_config(page_title="GDG Attendance Tracker", page_icon="🎟️", layout="centered")

# --- Google Colors ---
GOOGLE_BLUE = "#4285F4"
GOOGLE_RED = "#EA4335"
GOOGLE_YELLOW = "#FBBC05"
GOOGLE_GREEN = "#34A853"
GOOGLE_BG = "#F8F9FA"

# --- Custom Header ---
logo_path = 'logo.png'
header_cols = st.columns([0.25, 0.75])
with header_cols[0]:
    st.image(logo_path, width=110)
with header_cols[1]:
    st.markdown(
        f"""
        <div style='background: linear-gradient(90deg, {GOOGLE_BLUE} 0%, {GOOGLE_GREEN} 40%, {GOOGLE_YELLOW} 70%, {GOOGLE_RED} 100%); padding: 0.2rem 1rem; border-radius: 0 0 16px 16px; margin-bottom: 1.5rem; display: flex; align-items: center;'>
            <h1 style='color: white; margin: 0; display: inline; letter-spacing: 1px;'>GDG Attendance Tracker</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

# Show user profile in header
if st.session_state['user_email']:
    cols = st.columns([0.1, 0.9])
    with cols[0]:
        if st.session_state.get('user_picture'):
            st.image(st.session_state['user_picture'], width=48)
    with cols[1]:
        st.markdown(f"<span style='font-size:1.1rem; color:{GOOGLE_BLUE};'>Signed in as <b>{st.session_state.get('user_name', st.session_state['user_email'])}</b></span>", unsafe_allow_html=True)

# --- Sidebar Navigation ---
st.sidebar.markdown(f"<h2 style='color:{GOOGLE_BLUE};margin-bottom:0.5em;'>Navigation</h2>", unsafe_allow_html=True)
navigation_options = ['🏠 Home', '📅 Events', '📷 QR Scanner', '👤 Profile', '🏆 Leaderboard']
if st.session_state['user_email'] in ADMIN_EMAILS:
    navigation_options.append('🔐 QR Management')
page = st.sidebar.radio('Go to', navigation_options)

# Google Sign-In
if not st.session_state['user_email']:
    st.info('Please sign in with Google to use the app.')
    result = oauth2.authorize_button(
        name='Sign in with Google',
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        key='google',
        use_container_width=True
    )
    if result and 'token' in result:
        import jwt
        id_token = result['token']['id_token']
        decoded = jwt.decode(id_token, options={"verify_signature": False})
        st.session_state['user_email'] = decoded.get('email')
        st.session_state['user_name'] = decoded.get('name')
        st.session_state['user_picture'] = decoded.get('picture')
        st.success(f"Signed in as {st.session_state['user_email']}")
    st.stop()

def decode_qr_from_image(image):
    """Enhanced QR code detection with multiple preprocessing steps"""
    try:
        # Ensure image is in the correct format
        if image.dtype != np.uint8:
            if image.dtype == bool:
                image = (image * 255).astype(np.uint8)
            else:
                image = image.astype(np.uint8)
        
        # Try original image first
        detector = cv2.QRCodeDetector()
        data, bbox, _ = detector.detectAndDecode(image)
        
        if data and data.strip():
            return data.strip()
        
        # Try with different preprocessing methods
        preprocessing_methods = [
            ("Original", image),
            ("Inverted", cv2.bitwise_not(image)),
            ("Resized 2x", cv2.resize(image, (image.shape[1]*2, image.shape[0]*2))),
            ("Resized 3x", cv2.resize(image, (image.shape[1]*3, image.shape[0]*3))),
            ("Blurred", cv2.GaussianBlur(image, (3, 3), 0)),
            ("Sharpened", cv2.filter2D(image, -1, np.array([[-1,-1,-1], [-1,9,-1], [-1,-1,-1]]))),
            ("Threshold", cv2.threshold(image, 127, 255, cv2.THRESH_BINARY)[1]),
            ("Adaptive Threshold", cv2.adaptiveThreshold(image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2))
        ]
        
        for method_name, processed_image in preprocessing_methods:
            try:
                data, bbox, _ = detector.detectAndDecode(processed_image)
                if data and data.strip():
                    print(f"QR detected using {method_name} preprocessing")
                    return data.strip()
            except Exception as e:
                print(f"Error with {method_name} preprocessing: {e}")
                continue
        
        return None
    except Exception as e:
        print(f"QR detection error: {e}")
        return None

def get_event_by_name(event_name):
    event_query = db.collection('events').where('name', '==', event_name).limit(1).stream()
    return next(event_query, None)

def get_event_by_id(event_id):
    # For this prototype, event_id is the event name
    return get_event_by_name(event_id)

def generate_qr_code(data, event_name):
    """Generate QR code for event attendance tracking"""
    # Create QR code instance
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(data)
    qr.make(fit=True)
    
    # Create QR code image
    qr_image = qr.make_image(fill_color="black", back_color="white")
    
    # Convert to base64 for display
    buffered = io.BytesIO()
    qr_image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    
    return img_str, qr_image

if page == '🏠 Home':
    st.header('Welcome!')
    st.markdown("""<span style='color:#EA4335;font-weight:bold;'>📌 GSOC September 2025</span> | <span style='color:#34A853;'>📅 2025-09-15</span>""", unsafe_allow_html=True)
elif page == '📅 Events':
    st.markdown(f"<h2 style='color:{GOOGLE_RED};margin-bottom:0.5em;'>📅 Events</h2>", unsafe_allow_html=True)
    st.write('Browse upcoming and past events. Register or manage events below.')

    # Fetch events from Firestore
    with st.spinner('Loading events...'):
        events_ref = db.collection('events')
        events = events_ref.order_by('date', direction="DESCENDING").stream()
        event_list = []
        event_docs = []
        for event in events:
            data = event.to_dict()
            event_list.append(data)
            event_docs.append(event)

    if event_list:
        for i, event in enumerate(event_list):
            with st.container():
                st.markdown(f"""
                <div style='background: linear-gradient(90deg, {GOOGLE_BLUE} 0%, {GOOGLE_GREEN} 100%); border-left: 8px solid {GOOGLE_YELLOW}; border-radius: 12px; padding: 1rem; margin-bottom: 1rem; box-shadow: 0 2px 8px #0001;'>
                """, unsafe_allow_html=True)
                expander_title = f"📌 {event.get('name', 'No Name')} | 📅 {event.get('date', '')}"
                with st.expander(expander_title, expanded=True):
                    # Styled, colored, large event title inside the expander
                    st.markdown(f"<span style='color:{GOOGLE_RED};font-size:1.3em;font-weight:bold;'>📌 {event.get('name', 'No Name')}</span> | <span style='color:{GOOGLE_GREEN};font-size:1.1em;'>📅 {event.get('date', '')}</span>", unsafe_allow_html=True)
                    st.write(event.get('description', ''))
                    cols = st.columns([1, 1])
                    with cols[0]:
                        if st.session_state['user_email'] in ADMIN_EMAILS:
                            # Admin controls
                            admin_cols = st.columns([1, 1])
                            with admin_cols[0]:
                                if st.button(f"🗑️ Delete", key=f"delete_{i}"):
                                    event_docs[i].reference.delete()
                                    st.success(f"Event '{event.get('name', 'No Name')}' deleted. Please refresh to update the list.")
                            
                            with admin_cols[1]:
                                # QR Code Generation for Attendance
                                if st.button(f"📱 Generate QR", key=f"qr_{i}"):
                                    event_name = event.get('name', 'No Name')
                                    # Generate QR code with event name as data
                                    qr_data = f"GDG_ATTENDANCE_{event_name}_{datetime.now().strftime('%Y%m%d')}"
                                    qr_base64, qr_image = generate_qr_code(qr_data, event_name)
                                    
                                    st.markdown(f"<h4 style='color:{GOOGLE_GREEN};'>📱 Attendance QR Code for: {event_name}</h4>", unsafe_allow_html=True)
                                    st.markdown(f"""
                                    <div style='text-align:center; padding:1rem; background:white; border-radius:8px; border:2px solid {GOOGLE_BLUE};'>
                                        <img src="data:image/png;base64,{qr_base64}" style='max-width:300px;'>
                                        <p style='margin-top:0.5rem; color:#666; font-size:0.9em;'>Scan this QR code to mark attendance</p>
                                        <p style='color:#888; font-size:0.8em;'>Event: {event_name}</p>
                                        <p style='color:#888; font-size:0.8em;'>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}</p>
                                    </div>
                                    """, unsafe_allow_html=True)
                                    
                                    # Download button for QR code
                                    buffered = io.BytesIO()
                                    qr_image.save(buffered, format="PNG")
                                    st.download_button(
                                        label="📥 Download QR Code",
                                        data=buffered.getvalue(),
                                        file_name=f"attendance_qr_{event_name}_{datetime.now().strftime('%Y%m%d')}.png",
                                        mime="image/png",
                                        key=f"download_qr_{i}"
                                    )
                            
                            # Show registered users for this event
                            reg_ref = db.collection('registrations')
                            reg_query = reg_ref.where('event_name', '==', event.get('name', 'No Name'))
                            reg_docs = list(reg_query.stream())
                            if reg_docs:
                                st.markdown(f'<span style="color:{GOOGLE_BLUE};font-weight:bold;">👥 Registered Users:</span>', unsafe_allow_html=True)
                                for reg in reg_docs:
                                    reg_data = reg.to_dict()
                                    st.write(f"- {reg_data.get('user_email', '')} at {reg_data.get('timestamp', '')}")
                            else:
                                st.info('No users registered for this event yet.')
                        else:
                            # Registration for non-admins
                            user_email = st.session_state['user_email']
                            # Check if already registered
                            reg_ref = db.collection('registrations')
                            reg_query = reg_ref.where('user_email', '==', user_email).where('event_name', '==', event.get('name', 'No Name'))
                            reg_docs = list(reg_query.stream())
                            if reg_docs:
                                st.success('✅ You are already registered for this event.')
                            else:
                                if st.button(f"📝 Register", key=f"register_{i}"):
                                    db.collection('registrations').add({
                                        'user_email': user_email,
                                        'event_name': event.get('name', 'No Name'),
                                        'timestamp': datetime.now().isoformat()
                                    })
                                    st.success('Registered for event!')
                    st.markdown('---')
                st.markdown("</div>", unsafe_allow_html=True)
    else:
        st.info('No events found.')

    st.write('---')
    st.markdown(f"<h3 style='color:{GOOGLE_GREEN};margin-bottom:0.5em;'>➕ Add New Event (Admin Only)</h3>", unsafe_allow_html=True)
    if st.session_state['user_email'] in ADMIN_EMAILS:
        with st.form('add_event_form'):
            name = st.text_input('Event Name')
            date = st.date_input('Event Date', value=datetime.now())
            description = st.text_area('Description')
            submitted = st.form_submit_button('Add Event')
            if submitted and name:
                db.collection('events').add({
                    'name': name,
                    'date': date.strftime('%Y-%m-%d'),
                    'description': description
                })
                st.success('Event added! Please refresh to see the new event.')
    else:
        st.warning('Only admins can add new events. Contact the organizer if you need access.')
elif page == '📷 QR Scanner':
    st.markdown(f"<h2 style='color:{GOOGLE_YELLOW};margin-bottom:0.5em;'>📷 QR Code Scanner</h2>", unsafe_allow_html=True)
    st.write('Scan a QR code using your webcam or upload an image containing a QR code.')

    tab1, tab2 = st.tabs(["Webcam Scan", "Image Upload"])

    def mark_attendance(qr_data):
        # Parse QR code data to extract event information
        if qr_data.startswith('GDG_ATTENDANCE_'):
            # Extract event name from QR data
            parts = qr_data.split('_')
            if len(parts) >= 3:
                event_name = '_'.join(parts[2:-1])  # Everything between GDG_ATTENDANCE_ and date
                event_date = parts[-1] if len(parts) > 3 else 'Unknown'
                
                # Lookup event details
                event = get_event_by_name(event_name)
                if event:
                    event_data = event.to_dict()
                    st.success(f"✅ **Event Found:** {event_data.get('name', '')} | Date: {event_data.get('date', '')}")
                else:
                    st.warning(f'⚠️ Event "{event_name}" not found in database. Attendance will still be recorded.')
                
                st.markdown("---")
                st.subheader('📝 Attendance Marking')
                user_email = st.session_state['user_email']
                is_admin = user_email in ADMIN_EMAILS
                
                # Show user info with admin badge if applicable
                if is_admin:
                    st.write(f'**👤 User:** {user_email} 👑 **ADMIN**')
                else:
                    st.write(f'**👤 User:** {user_email}')
                
                st.write(f'**📅 Event:** {event_name}')
                st.write(f'**📱 QR Date:** {event_date}')
                
                # Check for duplicate attendance
                attendance_ref = db.collection('attendance')
                query = attendance_ref.where('user_email', '==', user_email).where('event_id', '==', event_name)
                docs = list(query.stream())
                if docs:
                    st.error('❌ **Already Marked:** You have already marked attendance for this event.')
                    st.write(f'**Previous attendance:** {docs[0].to_dict().get("timestamp", "Unknown")}')
                else:
                    # Auto-mark attendance for valid QR codes
                    try:
                        attendance_data = {
                            'user_email': user_email,
                            'event_id': event_name,
                            'qr_data': qr_data,
                            'timestamp': datetime.now().isoformat(),
                            'is_admin': is_admin
                        }
                        
                        db.collection('attendance').add(attendance_data)
                        
                        # Show success message with admin badge if applicable
                        if is_admin:
                            st.success('🎉 **Admin Attendance Marked Successfully!** 👑')
                        else:
                            st.success('🎉 **Attendance Marked Successfully!**')
                        
                        st.balloons()
                        st.write(f'**✅ Confirmed:** {user_email} has been marked present for {event_name}')
                        st.write(f'**⏰ Time:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')
                        
                        if is_admin:
                            st.info('👑 **Admin Note:** Your attendance has been recorded with admin privileges.')
                        
                        # Show a prominent success message
                        st.markdown("""
                        <div style='background: linear-gradient(90deg, #34A853, #4285F4); padding: 1rem; border-radius: 8px; color: white; text-align: center; margin: 1rem 0;'>
                            <h3>✅ ATTENDANCE CONFIRMED!</h3>
                            <p>Your attendance has been successfully recorded in the system.</p>
                        </div>
                        """, unsafe_allow_html=True)
                        
                    except Exception as e:
                        st.error(f'❌ **Error marking attendance:** {str(e)}')
            else:
                st.error('❌ **Invalid QR Code Format:** Please use a valid GDG attendance QR code.')
        else:
            # Handle legacy QR codes or other formats
            st.warning('⚠️ **Invalid QR Code:** This QR code is not a valid GDG attendance code.')
            st.write(f'**📱 Scanned Data:** {qr_data}')
            st.info('💡 **Tip:** Please use the official GDG attendance QR code generated by an admin.')

    with tab1:
        st.write("Use your webcam to scan a QR code.")
        run_webcam = st.button('Start Webcam Scanner')
        qr_result = st.empty()
        if run_webcam:
            cap = cv2.VideoCapture(0)
            st.info('Press Q in the webcam window to stop scanning.')
            found = False
            event_id = None
            while cap.isOpened() and not found:
                ret, frame = cap.read()
                if not ret:
                    st.error('❌ **Failed to access webcam.** Please check your camera permissions.')
                    break
                data = decode_qr_from_image(frame)
                if data:
                    qr_result.success(f'✅ **QR Code Detected:** {data}')
                    qr_data = data
                    found = True
                cv2.imshow('QR Scanner - Press Q to quit', frame)
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
            cap.release()
            cv2.destroyAllWindows()
            if not found:
                qr_result.info('🔍 **No QR code detected.** Please try again or check the QR code.')
            if qr_data:
                # Auto-mark attendance for webcam scans
                if qr_data.startswith('GDG_ATTENDANCE_'):
                    mark_attendance(qr_data)
                else:
                    st.warning("⚠️ **Not a GDG Attendance QR Code**")
                    st.info("This QR code is not for attendance marking.")

    with tab2:
        st.write("Upload an image containing a QR code.")
        
        # Add test QR code generation for debugging
        if st.session_state['user_email'] in ADMIN_EMAILS:
            with st.expander("🧪 Generate Test QR Code"):
                test_event = st.text_input("Test Event Name", value="Test_Event")
                if st.button("Generate Test QR"):
                    test_qr_data = f"GDG_ATTENDANCE_{test_event}_{datetime.now().strftime('%Y%m%d')}"
                    test_qr_base64, test_qr_image = generate_qr_code(test_qr_data, test_event)
                    
                    st.markdown(f"""
                    <div style='text-align:center; padding:1rem; background:white; border-radius:8px; border:2px solid {GOOGLE_BLUE};'>
                        <h4>🧪 Test QR Code</h4>
                        <img src="data:image/png;base64,{test_qr_base64}" style='max-width:200px;'>
                        <p><strong>Data:</strong> {test_qr_data}</p>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Download test QR code
                    buffered = io.BytesIO()
                    test_qr_image.save(buffered, format="PNG")
                    st.download_button(
                        label="📥 Download Test QR Code",
                        data=buffered.getvalue(),
                        file_name=f"test_qr_{test_event}.png",
                        mime="image/png"
                    )
        
        uploaded_file = st.file_uploader("Choose an image", type=["jpg", "jpeg", "png"])
        qr_data = None
        
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption='Uploaded Image', use_container_width=True)
            
            # Auto-scan QR code immediately after upload
            with st.spinner("🔍 Automatically scanning QR code..."):
                # Convert PIL image to proper format first
                if image.mode == '1':  # Binary/black and white image
                    # Convert binary image to grayscale
                    image = image.convert('L')
                    st.info("🔄 **Converted binary image to grayscale for better QR detection**")
                
                # Convert PIL image to OpenCV format properly
                image_array = np.array(image)
                
                # Debug: Show image properties
                st.write(f"**📊 Image Analysis:**")
                st.write(f"• **Size:** {image.size}")
                st.write(f"• **Mode:** {image.mode}")
                st.write(f"• **Array Shape:** {image_array.shape}")
                st.write(f"• **Array Type:** {image_array.dtype}")
                st.write(f"• **Value Range:** {image_array.min()} to {image_array.max()}")
                
                # Convert to OpenCV format with proper handling
                if len(image_array.shape) == 3:  # Color image
                    if image_array.dtype == np.uint8:
                        image_cv = cv2.cvtColor(image_array, cv2.COLOR_RGB2BGR)
                    else:
                        image_cv = cv2.cvtColor(image_array.astype(np.uint8), cv2.COLOR_RGB2BGR)
                else:  # Grayscale image
                    if image_array.dtype == np.uint8:
                        image_cv = image_array
                    else:
                        # Convert boolean or other types to uint8
                        if image_array.dtype == bool:
                            image_cv = (image_array * 255).astype(np.uint8)
                        else:
                            image_cv = image_array.astype(np.uint8)
                
                st.write(f"• **OpenCV Shape:** {image_cv.shape}")
                st.write(f"• **OpenCV Type:** {image_cv.dtype}")
                
                # Try to detect QR code with detailed feedback
                st.write("**🔍 Attempting QR Detection...**")
                data = decode_qr_from_image(image_cv)
                
                if data:
                    st.success(f'✅ **QR Code Detected:** {data}')
                    qr_data = data
                    
                    # Show QR code details
                    st.markdown("---")
                    st.subheader("📱 QR Code Information")
                    st.write(f"**Data:** {data}")
                    st.write(f"**Length:** {len(data)} characters")
                    
                    # Check if it's a valid GDG attendance QR code
                    if data.startswith('GDG_ATTENDANCE_'):
                        st.success("✅ **Valid GDG Attendance QR Code**")
                        # Auto-mark attendance immediately
                        mark_attendance(data)
                    else:
                        st.warning("⚠️ **Not a GDG Attendance QR Code**")
                        st.info("This QR code is not for attendance marking.")
                else:
                    st.error('❌ **No QR code detected** in the uploaded image.')
                    
                    # Enhanced troubleshooting
                    st.markdown("---")
                    st.subheader("🔧 Troubleshooting Guide")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.write("**📋 Common Issues:**")
                        st.write("• QR code too small or blurry")
                        st.write("• Poor lighting or shadows")
                        st.write("• QR code partially cut off")
                        st.write("• Image compression artifacts")
                        st.write("• Wrong image format")
                    
                    with col2:
                        st.write("**💡 Solutions:**")
                        st.write("• Use high-resolution images")
                        st.write("• Ensure good lighting")
                        st.write("• Center the QR code properly")
                        st.write("• Try different angles")
                        st.write("• Use PNG format if possible")
                    
                    # Test with a sample QR code
                    if st.session_state['user_email'] in ADMIN_EMAILS:
                        st.markdown("---")
                        st.subheader("🧪 Test QR Code")
                        if st.button("Generate Test QR for Testing"):
                            test_qr_data = f"GDG_ATTENDANCE_TestEvent_{datetime.now().strftime('%Y%m%d')}"
                            test_qr_base64, test_qr_image = generate_qr_code(test_qr_data, "TestEvent")
                            
                            st.markdown(f"""
                            <div style='text-align:center; padding:1rem; background:white; border-radius:8px; border:2px solid {GOOGLE_BLUE};'>
                                <h4>🧪 Test QR Code</h4>
                                <img src="data:image/png;base64,{test_qr_base64}" style='max-width:200px;'>
                                <p><strong>Data:</strong> {test_qr_data}</p>
                            </div>
                            """, unsafe_allow_html=True)
                            
                            st.info("📱 **Download this test QR code and upload it to test the scanner!**")
                            
                            # Download test QR code
                            buffered = io.BytesIO()
                            test_qr_image.save(buffered, format="PNG")
                            st.download_button(
                                label="📥 Download Test QR Code",
                                data=buffered.getvalue(),
                                file_name="test_qr_code.png",
                                mime="image/png"
                            )
elif page == '👤 Profile':
    st.markdown(f"<h2 style='color:{GOOGLE_GREEN};margin-bottom:0.5em;'>👤 User Profile</h2>", unsafe_allow_html=True)
    user_email = st.session_state['user_email']
    st.write(f'**Name:** {st.session_state.get("user_name", user_email)}')
    if st.session_state.get('user_picture'):
        st.image(st.session_state['user_picture'], width=80)
    # Fetch attendance records for this user
    with st.spinner('Loading your attendance...'):
        attendance_ref = db.collection('attendance').where('user_email', '==', user_email)
        attendance_docs = list(attendance_ref.stream())
    st.write(f'**Events Attended:** {len(attendance_docs)}')
    if attendance_docs:
        st.subheader('Attended Events:')
        for att in attendance_docs:
            att_data = att.to_dict()
            event = get_event_by_id(att_data.get('event_id', ''))
            if event:
                event_data = event.to_dict()
                st.write(f"- {event_data.get('name', '')} ({event_data.get('date', '')}) at {att_data.get('timestamp', '')}")
            else:
                st.write(f"- Event ID: {att_data.get('event_id', '')} at {att_data.get('timestamp', '')}")
    else:
        st.info('No attendance records found.')
    # Show registered events
    with st.spinner('Loading your registrations...'):
        reg_ref = db.collection('registrations').where('user_email', '==', user_email)
        reg_docs = list(reg_ref.stream())
    st.write(f'**Events Registered:** {len(reg_docs)}')
    if reg_docs:
        st.subheader('Registered Events:')
        for reg in reg_docs:
            reg_data = reg.to_dict()
            event = get_event_by_name(reg_data.get('event_name', ''))
            if event:
                event_data = event.to_dict()
                st.write(f"- {event_data.get('name', '')} ({event_data.get('date', '')}) at {reg_data.get('timestamp', '')}")
            else:
                st.write(f"- Event: {reg_data.get('event_name', '')} at {reg_data.get('timestamp', '')}")
elif page == '🏆 Leaderboard':
    st.markdown(f"<h2 style='color:{GOOGLE_BLUE};margin-bottom:0.5em;'>🏆 Leaderboard</h2>", unsafe_allow_html=True)
    st.write('Top attendees ranked by number of events attended:')
    # Fetch all attendance records
    with st.spinner('Loading leaderboard...'):
        attendance_ref = db.collection('attendance')
        attendance_docs = list(attendance_ref.stream())
    if attendance_docs:
        user_counts = Counter()
        user_events = {}
        for att in attendance_docs:
            att_data = att.to_dict()
            user = att_data.get('user_email', 'Unknown')
            user_counts[user] += 1
            user_events.setdefault(user, []).append(att_data.get('event_id', ''))
        sorted_users = user_counts.most_common()
        leaderboard = []
        for i, (user, count) in enumerate(sorted_users):
            events = user_events[user]
            event_names = []
            for eid in events:
                event = get_event_by_id(eid)
                if event:
                    event_data = event.to_dict()
                    event_names.append(event_data.get('name', eid))
                else:
                    event_names.append(eid)
            leaderboard.append({'Rank': i+1, 'User': user, 'Events Attended': count, 'Events': ', '.join(event_names)})
        st.table(leaderboard)
    else:
        st.info('No attendance records found.')
elif page == '🔐 QR Management':
    st.markdown(f"<h2 style='color:{GOOGLE_RED};margin-bottom:0.5em;'>🔐 QR Code Management (Admin Only)</h2>", unsafe_allow_html=True)
    st.write('Generate and manage attendance QR codes for events.')
    
    if st.session_state['user_email'] not in ADMIN_EMAILS:
        st.error('Access denied. Only administrators can access this page.')
        st.stop()
    
    # Fetch all events
    with st.spinner('Loading events...'):
        events_ref = db.collection('events')
        events = events_ref.order_by('date', direction="DESCENDING").stream()
        event_list = []
        for event in events:
            data = event.to_dict()
            event_list.append(data)
    
    if event_list:
        st.markdown(f"<h3 style='color:{GOOGLE_GREEN};'>📱 Generate Attendance QR Codes</h3>", unsafe_allow_html=True)
        
        # Event selection for QR generation
        selected_event = st.selectbox(
            'Select an event to generate QR code:',
            options=[event.get('name', 'No Name') for event in event_list],
            format_func=lambda x: f"{x} ({next((e.get('date', '') for e in event_list if e.get('name') == x), '')})"
        )
        
        if selected_event:
            st.markdown(f"<h4 style='color:{GOOGLE_BLUE};'>Event: {selected_event}</h4>", unsafe_allow_html=True)
            
            # Generate QR code on demand
            if st.button('🔄 Generate New QR Code', key='generate_new_qr'):
                event_name = selected_event
                qr_data = f"GDG_ATTENDANCE_{event_name}_{datetime.now().strftime('%Y%m%d')}"
                qr_base64, qr_image = generate_qr_code(qr_data, event_name)
                
                # Display QR code with event details
                st.markdown(f"""
                <div style='text-align:center; padding:2rem; background:white; border-radius:12px; border:3px solid {GOOGLE_BLUE}; box-shadow: 0 4px 12px rgba(0,0,0,0.1);'>
                    <h3 style='color:{GOOGLE_GREEN}; margin-bottom:1rem;'>📱 GDG Attendance QR Code</h3>
                    <img src="data:image/png;base64,{qr_base64}" style='max-width:400px; border-radius:8px;'>
                    <div style='margin-top:1rem; padding:1rem; background:#f8f9fa; border-radius:8px;'>
                        <p style='margin:0.5rem 0; color:#333;'><strong>Event:</strong> {event_name}</p>
                        <p style='margin:0.5rem 0; color:#666;'><strong>Generated:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                        <p style='margin:0.5rem 0; color:#888; font-size:0.9em;'><strong>QR Data:</strong> {qr_data}</p>
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
                # Download options
                col1, col2 = st.columns(2)
                with col1:
                    buffered = io.BytesIO()
                    qr_image.save(buffered, format="PNG")
                    st.download_button(
                        label="📥 Download QR Code (PNG)",
                        data=buffered.getvalue(),
                        file_name=f"gdg_attendance_{event_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.png",
                        mime="image/png",
                        key="download_qr_png"
                    )
                
                with col2:
                    # Save QR data to text file
                    qr_info = f"""GDG Attendance QR Code Information
Event: {event_name}
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
QR Data: {qr_data}
Instructions: Scan this QR code to mark attendance for the event.
"""
                    st.download_button(
                        label="📄 Download QR Info (TXT)",
                        data=qr_info,
                        file_name=f"qr_info_{event_name}_{datetime.now().strftime('%Y%m%d_%H%M')}.txt",
                        mime="text/plain",
                        key="download_qr_info"
                    )
        
        # Show recent attendance records
        st.markdown(f"<h3 style='color:{GOOGLE_YELLOW}; margin-top:2rem;'>📊 Recent Attendance Records</h3>", unsafe_allow_html=True)
        with st.spinner('Loading attendance records...'):
            attendance_ref = db.collection('attendance')
            attendance_docs = list(attendance_ref.order_by('timestamp', direction="DESCENDING").limit(20).stream())
        
        if attendance_docs:
            attendance_data = []
            for att in attendance_docs:
                att_data = att.to_dict()
                attendance_data.append({
                    'User': att_data.get('user_email', 'Unknown'),
                    'Event': att_data.get('event_id', 'Unknown'),
                    'Timestamp': att_data.get('timestamp', 'Unknown'),
                    'QR Data': att_data.get('qr_data', 'Legacy')
                })
            
            st.dataframe(attendance_data, use_container_width=True)
        else:
            st.info('No attendance records found.')
    else:
        st.info('No events found. Please create events first to generate QR codes.')

# --- Footer ---
st.markdown(
    """
    <hr style='margin-top:2rem;margin-bottom:0.5rem;'>
    <div style='text-align:center; color: #888;'>
        <small>Made with ❤️ for GDG | Powered by GDG IIMT College of Engineering Greater Noida</small>
    </div>
    """,
    unsafe_allow_html=True
) 