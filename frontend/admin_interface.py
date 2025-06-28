import streamlit as st
from backend.auth_manager import AuthManager

class AdminInterface:
    def __init__(self):
        self.auth_manager = AuthManager()
    
    def render(self):
        """Render the admin interface"""
        st.title("🔧 Admin Panel")
        st.write("Manage users and system settings")
        
        # Check if current user is admin
        user_data = st.session_state.get("user_data", {})
        if not user_data.get("is_admin", False):
            st.error("Access denied. Admin privileges required.")
            return
        
        # Admin tabs
        tab1, tab2 = st.tabs(["User Management", "System Info"])
        
        with tab1:
            self.render_user_management()
        
        with tab2:
            self.render_system_info()
    
    def render_user_management(self):
        """Render user management section"""
        st.subheader("User Management")
        
        # Get all users
        users = self.auth_manager.get_all_users()
        
        if not users:
            st.info("No users found.")
            return
        
        # Display users in a table
        st.write("**Registered Users:**")
        
        for user in users:
            with st.expander(f"{user['username']} ({user['email']})"):
                col1, col2 = st.columns([3, 1])
                
                with col1:
                    st.write(f"**ID:** {user['id']}")
                    st.write(f"**Username:** {user['username']}")
                    st.write(f"**Email:** {user['email']}")
                    st.write(f"**Admin:** {'Yes' if user['is_admin'] else 'No'}")
                    st.write(f"**Created:** {user['created_at']}")
                    if user['last_login']:
                        st.write(f"**Last Login:** {user['last_login']}")
                
                with col2:
                    # Don't allow admin to delete themselves
                    if user['id'] != st.session_state.get("user_data", {}).get("id"):
                        if st.button(f"Delete {user['username']}", key=f"delete_{user['id']}"):
                            success, message = self.auth_manager.delete_user(user['id'])
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.write("**Current User**")
    
    def render_system_info(self):
        """Render system information"""
        st.subheader("System Information")
        
        # Get system stats
        users = self.auth_manager.get_all_users()
        admin_count = sum(1 for user in users if user['is_admin'])
        regular_user_count = len(users) - admin_count
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Users", len(users))
        
        with col2:
            st.metric("Admin Users", admin_count)
        
        with col3:
            st.metric("Regular Users", regular_user_count)
        
        # Admin credentials reminder
        st.info("""
        **Default Admin Credentials:**
        - Username: `admin`
        - Email: `admin@admin.com`
        - Password: `admin123`
        
        **⚠️ Important:** Change the default admin password after first login!
        """)
