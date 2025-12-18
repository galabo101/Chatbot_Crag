import streamlit as st
import pandas as pd
import plotly.express as px
import time
from src.admin_backend import get_chat_stats, get_top_keywords, process_uploaded_file, get_all_files, delete_doc, sync_documents_from_qdrant, get_file_details

def render_admin_dashboard():
    st.header("🛠️ Trang Quản Trị Hệ Thống")  
    tab1, tab2, tab3 = st.tabs(["📊 Thống kê & Xu hướng", "📚 Cập nhật Kiến thức", "🗑️ Quản lý dữ liệu"])
    
    with tab1: # TAB 1 THỐNG KÊ
        try:
            stats = get_chat_stats()
            col1, col2 = st.columns(2)
            col1.metric("Tổng cuộc hội thoại", stats['total_conversations'])
            col2.metric("Tổng tin nhắn", stats['total_messages'])            
            st.divider()
            
            # Biểu đồ từ khoá
            st.subheader("🔥 Chủ đề được quan tâm nhất")
            top_keywords = get_top_keywords()
            if top_keywords:
                df_kw = pd.DataFrame(top_keywords, columns=['Từ khóa', 'Số lần'])
                fig = px.bar(df_kw, x='Từ khóa', y='Số lần', color='Số lần')
                st.plotly_chart(fig, use_container_width=True)
            
            # Bảng câu hỏi gần đây
            st.subheader("💬 Câu hỏi gần đây")
            if not stats['recent_questions'].empty:
                st.dataframe(stats['recent_questions'], use_container_width=True, height=300)
            else:
                st.info("Chưa có dữ liệu câu hỏi.")
                
        except Exception as e:
            st.error(f"Không thể tải thống kê: {str(e)}")
    
    with tab2: # TAB 2 update DB  
        
        if "uploader_key" not in st.session_state:
            st.session_state.uploader_key = 0
            
        uploaded_files = st.file_uploader(
            "Upload tài liệu mới (PDF, Word, Excel, JSON, Ảnh (PNG/JPG)) - Tối đa 3 file/lần", 
            type=['pdf', 'docx', 'txt', 'xlsx', 'json', 'png', 'jpg', 'jpeg'],
            key=f"uploader_{st.session_state.uploader_key}",
            accept_multiple_files=True
        )
        
        if uploaded_files:
                       
            st.divider()
            
            # Validation logic
            is_valid_count = len(uploaded_files) <= 3
            btn_disabled = not is_valid_count
            btn_help = "⛔ Chỉ được phép tải lên tối đa 3 file. Vui lòng bỏ bớt file." if not is_valid_count else "Bắt đầu xử lý các file đã chọn"
            
            if st.button("🚀 Bắt đầu Xử lý & Cập nhật", type="primary", disabled=btn_disabled, help=btn_help):
                
                total_chunks = 0
                processed_count = 0
                
                with st.status("Đang xử lý dữ liệu...", expanded=True) as status:
                    # Loop qua từng file
                    for i, file in enumerate(uploaded_files):
                        status.write(f"📂 Đang xử lý file {i+1}/{len(uploaded_files)}: **{file.name}**...")
                        
                        try:
                            # Reuse pipeline components
                            client = None
                            model = None
                            if "pipeline" in st.session_state and st.session_state.pipeline:
                                client = st.session_state.pipeline.retriever.client
                                model = st.session_state.pipeline.retriever.model
                            
                            # Process single file
                            chunks = process_uploaded_file(file, client=client, model=model)
                            total_chunks += chunks
                            processed_count += 1
                            st.write(f"✅ Đã thêm {chunks} chunks từ {file.name}")
                            
                        except Exception as e:
                            st.error(f"❌ Lỗi xử lý {file.name}: {str(e)}")
                    
                    if processed_count == len(uploaded_files):
                        status.update(label="✅ Tất cả hoàn tất!", state="complete", expanded=False)
                        st.success(f"Thành công! Tổng cộng đã thêm **{total_chunks}** phân đoạn mới.")
                        st.balloons()
                        time.sleep(1.5)
                        st.session_state.uploader_key += 1
                        st.rerun()
                    else:
                        status.update(label="⚠️ Hoàn tất một phần", state="error")

    with tab3: # TAB 3 QUẢN LÝ DỮ LIỆU
        st.subheader("🗑️ Quản lý & Xóa Dữ liệu")
        st.warning("⚠️ Lưu ý: Hành động xóa sẽ gỡ bỏ hoàn toàn dữ liệu của file khỏi bộ nhớ Chatbot và không thể hoàn tác.")
        
        # Lấy client từ session
        client = None
        if "pipeline" in st.session_state and st.session_state.pipeline:
            client = st.session_state.pipeline.retriever.client

        # Toolbar
        if st.button("🔄 Làm mới & Đồng bộ", use_container_width=True):
             with st.spinner("Đang đồng bộ dữ liệu..."):
                sync_documents_from_qdrant(client=client)
                st.rerun()
            
        all_files = get_all_files(client=client)
        
        if not all_files:
            st.info("Hiện chưa có tài liệu nào trong cơ sở dữ liệu.")
        else:
            # --- INSPECTION VIEW (Moved to top) ---
            if "inspect_file" in st.session_state and st.session_state.inspect_file:
                st.divider()
                target_file = st.session_state.inspect_file
                st.subheader(f"🔍 Chi tiết: {target_file}")
                
                col_close, _ = st.columns([0.2, 0.8])
                if col_close.button("❌ Đóng chi tiết", type="secondary"):
                    st.session_state.inspect_file = None
                    st.rerun()

                with st.spinner("Đang tải chunks từ vector DB..."):
                    chunks = get_file_details(target_file, client=client)
                
                if chunks:
                    st.info(f"Tìm thấy **{len(chunks)}** phân đoạn.")
                    df_chunks = pd.DataFrame(chunks)
                    st.dataframe(df_chunks[["chunk_id", "length", "content", "type"]], use_container_width=True, height=300)
                else:
                    st.warning(f"Không tìm thấy dữ liệu chunks nào cho file: {target_file}")
                
                st.divider()
            # --------------------------------------

            st.write(f"Tìm thấy **{len(all_files)}** tài liệu:")
            
            # Header
            col1, col2, col3, col4 = st.columns([0.5, 0.25, 0.1, 0.15])
            col1.markdown("**Tên file**")
            col2.markdown("**Thời gian upload**")
            col3.markdown("**Chunks**")
            col4.markdown("**Thao tác**")
            st.divider()

            # Tạo bảng danh sách file
            for i, doc in enumerate(all_files):
                file_name = doc.get("filename", "Unknown")
                
                col1, col2, col3, col4 = st.columns([0.5, 0.25, 0.1, 0.15])
                with col1:
                    st.text(file_name)
                with col2:
                    st.text(doc.get("upload_time", "N/A"))
                with col3:
                    st.text(doc.get("num_chunks", "?"))    
                with col4:
                    c_del, c_ins = st.columns(2)
                    with c_del:
                        if st.button("🗑️", key=f"del_{i}", type="primary", use_container_width=True, help="Xóa file"):
                            try:
                                delete_doc(file_name, client=client)
                                st.toast(f"✅ Đã xóa: {file_name}", icon="🗑️")
                                time.sleep(1) 
                                st.rerun()
                            except Exception as e:
                                st.error(f"Lỗi khi xóa: {e}")
                    with c_ins:
                         # Callback function để set state an toàn hơn
                         def set_inspect(f):
                             st.session_state.inspect_file = f
                         
                         if st.button("👁️", key=f"ins_{i}", use_container_width=True, help="Chi tiết", on_click=set_inspect, args=(file_name,)):
                             pass