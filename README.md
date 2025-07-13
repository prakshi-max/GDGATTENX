# GDG Attendance Tracker

A comprehensive attendance tracking system built for Google Developer Groups (GDG) using Streamlit, Firebase, and QR code technology.

## 🎯 Project Overview

The GDG Attendance Tracker is a modern web application that streamlines event attendance management for Google Developer Groups. It features QR code generation, automatic attendance marking, and comprehensive admin tools.

## ✨ Key Features

### 🔐 Admin Features
- **QR Code Generation**: Generate unique QR codes for each event
- **Event Management**: Create, edit, and delete events
- **Attendance Monitoring**: View real-time attendance records
- **Admin Dashboard**: Comprehensive management interface

### 📱 User Features
- **QR Code Scanning**: Scan QR codes to mark attendance automatically
- **Profile Management**: View attendance history and registrations
- **Event Registration**: Register for upcoming events
- **Leaderboard**: See top attendees

### 🔧 Technical Features
- **Google OAuth**: Secure authentication with Google accounts
- **Firebase Integration**: Real-time database with Firestore
- **QR Code Technology**: Industry-standard QR code generation and scanning
- **Responsive Design**: Works on desktop and mobile devices

## 🛠️ Technology Stack

- **Frontend**: Streamlit (Python web framework)
- **Backend**: Firebase Firestore (NoSQL database)
- **Authentication**: Google OAuth 2.0
- **QR Code**: OpenCV + qrcode library
- **Deployment**: Streamlit Cloud

## 🚀 Live Demo

**Project Link**: [GDG Attendance Tracker](https://gdg-attendance-tracker.streamlit.app)

## 📋 Setup Instructions

### Prerequisites
- Python 3.8+
- Firebase project with Firestore enabled
- Google OAuth credentials

### Installation
1. Clone the repository
2. Install dependencies: `pip install -r requirements.txt`
3. Set up Firebase credentials
4. Configure Google OAuth
5. Run: `streamlit run app.py`

## 🔧 Configuration

### Environment Variables
- `GOOGLE_CLIENT_ID`: Google OAuth client ID
- `GOOGLE_CLIENT_SECRET`: Google OAuth client secret
- Firebase service account key

### Firebase Setup
1. Create a Firebase project
2. Enable Firestore database
3. Generate service account key
4. Update `firebase_admin_init.py`

## 📊 Database Schema

### Collections
- **events**: Event information and details
- **attendance**: Attendance records with timestamps
- **registrations**: User event registrations
- **users**: User profiles and preferences

## 🎯 Use Cases

- **GDG Events**: Track attendance at workshops, meetups, and conferences
- **Educational Institutions**: Manage student attendance
- **Corporate Events**: Monitor employee participation
- **Community Gatherings**: Track member engagement

## 🔒 Security Features

- Google OAuth authentication
- Admin-only QR code generation
- Secure Firebase rules
- Input validation and sanitization

## 📱 Mobile Compatibility

The application is fully responsive and works seamlessly on:
- Desktop browsers
- Mobile devices
- Tablets

## 🎉 Project Highlights

- **Real-time Updates**: Live attendance tracking
- **User-friendly Interface**: Intuitive design with Google Material Design
- **Scalable Architecture**: Built for growth and expansion
- **Professional UI**: Modern, clean interface with GDG branding

## 👨‍💻 Developer

**Name**: [Your Name]  
**Institution**: GDG IIMT College of Engineering Greater Noida  
**Project**: GDG Attendance Tracker  
**Technology**: Python, Streamlit, Firebase, QR Codes

## 📄 License

This project is developed for educational purposes and GDG community use.

---

**Made with ❤️ for GDG | Powered by GDG IIMT College of Engineering Greater Noida** 