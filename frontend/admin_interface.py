import streamlit as st
from backend.auth_manager import AuthManager
from backend.vector_store import VectorStoreManager
from backend.qa_chain import QAChain

class AdminInterface:
    def __init__(self):
        self.auth_manager = AuthManager()
        self.vector_store_manager = VectorStoreManager()
        self.qa_chain = QAChain()
    
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
        tab1, tab2, tab3 = st.tabs(["User Management", "Database Management", "System Info"])
        
        with tab1:
            self.render_user_management()
        
        with tab2:
            self.render_database_management()
        
        with tab3:
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
            with st.expander(f" {user['username']} ({user['email']})"):
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
    
    def render_database_management(self):
        """Render database management section"""
        st.subheader("Database Management")
        st.write("Manage the Pinecone vector database")
        
        try:
            # Get database statistics
            stats = self.vector_store_manager.get_database_stats()
            
            # Display statistics
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Total Vectors", stats['total_vectors'])
            
            with col2:
                st.metric("Vector Dimension", stats['total_dimension'])
            
            with col3:
                st.metric("Index Fullness", f"{stats['index_fullness']:.2%}")
            
            # User statistics
            st.write("**Documents by User:**")
            for username, count in stats['user_stats'].items():
                st.write(f"- {username}: {count} documents")
            
            st.write("---")
            
            # Database actions - now stacked vertically
            st.write("Database Actions:")
            
            # First action: Delete specific user documents
            st.write(" Delete User Documents:")
            
            if stats['user_stats']:
                selected_user = st.selectbox(
                    "Select user to delete documents:",
                    options=list(stats['user_stats'].keys()),
                    key="user_delete_select"
                )
                
                if st.button(f"🗑️ Delete {selected_user}'s Documents", type="secondary", use_container_width=True):
                    if st.checkbox(f"I understand this will delete ALL documents for user '{selected_user}'"):
                        with st.spinner(f"Deleting {selected_user}'s documents..."):
                            try:
                                deleted_count = self.vector_store_manager.delete_user_documents(selected_user)
                                st.success(f"✅ Deleted {deleted_count} documents for user '{selected_user}'!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Error deleting user documents: {str(e)}")
            else:
                st.info("ℹ️ No user documents found in the database.")
                st.button("🗑️ Delete User Documents", type="secondary", use_container_width=True, disabled=True)
            
            st.write("---")
            
            # Second action: Clear entire database
            st.write(" Clear Entire Database:")
            if st.button("🗑️ Clear Entire Database", type="secondary", use_container_width=True):
                # Show the deletion dialog
                st.session_state.show_delete_dialog = True
            
            # Render deletion dialog if needed
            if st.session_state.get("show_delete_dialog", False):
                self.render_delete_dialog(stats)
        
        except Exception as e:
            st.error(f"Error accessing database: {str(e)}")
    
    def render_delete_dialog(self, stats):
        """Render the database deletion confirmation dialog"""
        # Create a modal-like dialog using columns and containers
        st.markdown("---")
        
        # Warning dialog
        with st.container():
            st.markdown("""
            <div style="
                background-color: #fff3cd;
                border: 1px solid #ffeaa7;
                border-radius: 8px;
                padding: 20px;
                margin: 10px 0;
                box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            ">
            """, unsafe_allow_html=True)
            
            st.markdown("""
            <div style="text-align: center;">
                <h3 style="color: #856404; margin-bottom: 15px;">⚠️ WARNING: Database Deletion</h3>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div style="color: #856404; margin-bottom: 20px;">
                <p><strong>You are about to delete ALL documents from the database!</strong></p>
                <p>This action will permanently remove:</p>
                <ul>
                    <li><strong>{stats['total_vectors']}</strong> total vectors</li>
                    <li>All user documents and embeddings</li>
                    <li>All chat history and knowledge base</li>
                </ul>
                <p><strong>This action cannot be undone!</strong></p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("</div>", unsafe_allow_html=True)
            
            # Action buttons
            col1, col2, col3 = st.columns([1, 1, 1])
            
            with col1:
                if st.button("❌ Cancel", type="secondary", use_container_width=True):
                    st.session_state.show_delete_dialog = False
                    st.rerun()
            
            with col2:
                st.write("")  # Spacer
            
            with col3:
                if st.button("🗑️ Delete Anyway", type="primary", use_container_width=True):
                    # Perform the deletion
                    with st.spinner("Clearing database..."):
                        try:
                            # Show current status
                            st.write(f"📊 **Before deletion:** {stats['total_vectors']} vectors")
                            
                            # Perform deletion
                            deleted_count = self.vector_store_manager.clear_database()
                            st.write(f"🗑️ **Deleted:** {deleted_count} vectors")
                            
                            # Check after deletion
                            stats_after = self.vector_store_manager.get_database_stats()
                            st.write(f"📊 **After deletion:** {stats_after['total_vectors']} vectors")
                            
                            if stats_after['total_vectors'] == 0:
                                st.success("✅ Database cleared successfully!")
                            else:
                                st.warning(f"⚠️ **Warning:** {stats_after['total_vectors']} vectors still remain")
                            
                            # Close dialog and refresh
                            st.session_state.show_delete_dialog = False
                            st.rerun()
                            
                        except Exception as e:
                            st.error(f"❌ Error clearing database: {str(e)}")
                            st.session_state.show_delete_dialog = False
    
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
        
        # Database information
        try:
            stats = self.vector_store_manager.get_database_stats()
            st.write("**Database Information:**")
            st.write(f"- Total vectors: {stats['total_vectors']}")
            st.write(f"- Vector dimension: {stats['total_dimension']}")
            st.write(f"- Index fullness: {stats['index_fullness']:.2%}")
        except Exception as e:
            st.warning(f"Could not retrieve database information: {str(e)}")
