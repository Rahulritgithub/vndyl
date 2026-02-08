import streamlit as st
import pandas as pd
from io import BytesIO
from matplotlib import pyplot as plt


st.set_page_config(page_title="Active Job Tracker", layout="wide")

st.title("📊 Active Job & Interview Tracker")

# ------------------ Helper Functions ------------------
def read_file(file):
    name = file.name.lower()
    if name.endswith(".csv"):
        return pd.read_csv(file)
    return pd.read_excel(file, engine="openpyxl")


def to_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df.to_excel(writer, index=False)
    return output.getvalue()


# ------------------ Tabs ------------------
tab1, tab2 = st.tabs(["📂 Active Extract", "🔍 Compare Old vs New"])


# =====================================================
# TAB 1: SINGLE FILE – ACTIVE EXTRACT
# =====================================================
with tab1:
    st.subheader("📂 Extract Active Requests from Single File")

    uploaded_file = st.file_uploader(
        "Upload Excel or CSV File",
        type=["xlsx", "xls", "csv"],
        key="single"
    )

    if uploaded_file:
        df = read_file(uploaded_file)

        if "Status" not in df.columns:
            st.error("❌ 'Status' column not found.")
        else:
            active_df = df[
                df["Status"].astype(str).str.strip().str.lower() == "active"
            ].copy()

            # Add Hiring Manager column if missing
            if "Hiring Manager" not in active_df.columns:
                active_df["Hiring Manager"] = ""

            st.subheader("🔍 Preview: Active Requests")

            if active_df.empty:
                st.warning("No Active records found.")
            else:
                st.dataframe(active_df, use_container_width=True)

                st.download_button(
                    "⬇️ Download Active Requests",
                    data=to_excel(active_df),
                    file_name="active_requests.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                )

                st.success(f"✅ {len(active_df)} Active requests extracted")


with tab2:
    st.subheader("🔍 Compare OLD vs NEW Files - Active Status Tracking")

    col1, col2 = st.columns(2)

    with col1:
        old_file = st.file_uploader(
            "Upload OLD Excel",
            type=["xlsx", "xls", "csv"],
            key="old"
        )

    with col2:
        new_file = st.file_uploader(
            "Upload NEW Excel",
            type=["xlsx", "xls", "csv"],
            key="new"
        )

    if old_file and new_file:
        if st.button("🔍 Extract Active Statuses from Both Files"):
            # ---------- READ FILES ----------
            old_df = read_file(old_file)
            new_df = read_file(new_file)

            # ---------- VALIDATE ----------
            for col in ["Request ID", "Status"]:
                if col not in old_df.columns or col not in new_df.columns:
                    st.error(f"❌ '{col}' column missing in one of the files")
                    st.stop()

            # ---------- NORMALIZE DATA ----------
            for df in [old_df, new_df]:
                df["Request ID"] = (
                    df["Request ID"]
                    .astype(str)
                    .str.replace(".0", "", regex=False)
                    .str.strip()
                )
                df["Status"] = df["Status"].astype(str).str.strip().str.lower()

            # ---------- DEFINE ACTIVE STATUS PATTERNS ----------
            active_status_patterns = ["active", "partially", "zero", "filled"]
            pattern = '|'.join(active_status_patterns)

            # ---------- EXTRACT ACTIVE STATUSES FROM BOTH FILES ----------
            # From OLD file
            old_active = old_df[
                old_df["Status"].str.contains(pattern, case=False, na=False)
            ].copy()
            
            # From NEW file
            new_active = new_df[
                new_df["Status"].str.contains(pattern, case=False, na=False)
            ].copy()

            # ---------- CHECK IF WE FOUND ANY ACTIVE STATUSES ----------
            st.write("📊 **Active Status Records Found:**")
            col_old, col_new = st.columns(2)
            
            with col_old:
                st.metric("OLD File", len(old_active))
                if not old_active.empty:
                    st.write("Statuses in OLD:", old_active["Status"].unique())
            
            with col_new:
                st.metric("NEW File", len(new_active))
                if not new_active.empty:
                    st.write("Statuses in NEW:", new_active["Status"].unique())

            if old_active.empty and new_active.empty:
                st.warning("⚠️ No active status records found in either file!")
                st.stop()

            # ---------- CREATE COMPARISON DATAFRAME ----------
            comparison_data = []
            
            # Add records from OLD file
            for _, row in old_active.iterrows():
                comparison_data.append({
                    "Source": "OLD",
                    "Request ID": row["Request ID"],
                    "Status": row["Status"],
                    "Hiring Manager": row.get("Hiring Manager", ""),
                    "Job Title": row.get("Job Title", ""),
                    "Interviewed?": row.get("Interviewed?", ""),
                    "Work Site Name": row.get("Work Site Name", ""),
                    "Total Positions": row.get("Total Positions", "")
                })
            
            # Add records from NEW file
            for _, row in new_active.iterrows():
                comparison_data.append({
                    "Source": "NEW",
                    "Request ID": row["Request ID"],
                    "Status": row["Status"],
                    "Hiring Manager": row.get("Hiring Manager", ""),
                    "Job Title": row.get("Job Title", ""),
                    "Interviewed?": row.get("Interviewed?", ""),
                    "Work Site Name": row.get("Work Site Name", ""),
                    "Total Positions": row.get("Total Positions", "")
                })
            
            comparison_df = pd.DataFrame(comparison_data)
            
            # ---------- STANDARDIZE STATUS NAMES ----------
            status_mapping = {
                "partiallyfilled": "partially filled",
                "partially-filled": "partially filled",
                "zerofilled": "zero filled",
                "zero-filled": "zero filled"
            }
            
            comparison_df["Status"] = (
                comparison_df["Status"]
                .replace(status_mapping)
                .str.title()
            )

            # ---------- CREATE FINAL DOWNLOAD DATAFRAME ----------
            # This will contain Active, Partially Filled, Zero Filled from BOTH files
            final_download_df = comparison_df.copy()
            
            # Add source identification
            final_download_df["File Source"] = final_download_df["Source"]
            
            # Sort by Status then Request ID
            status_order = {
                "Active": 1,
                "Partially Filled": 2,
                "Zero Filled": 3
            }
            
            final_download_df["Status_Order"] = (
                final_download_df["Status"]
                .map(status_order)
                .fillna(99)
            )
            
            final_download_df = final_download_df.sort_values(["Status_Order", "Request ID"])
            final_download_df = final_download_df.drop("Status_Order", axis=1)
            final_download_df = final_download_df.reset_index(drop=True)

            # ---------- CREATE MERGED VIEW FOR COMPARISON ----------
            # Create a merged view showing OLD vs NEW side by side
            if not old_active.empty and not new_active.empty:
                # Pivot to compare OLD vs NEW
                pivot_df = comparison_df.pivot_table(
                    index="Request ID",
                    columns="Source",
                    values=["Status", "Hiring Manager"],
                    aggfunc='first'
                )
                
                # Flatten column names
                pivot_df.columns = [f"{col[1]}_{col[0]}" for col in pivot_df.columns]
                pivot_df = pivot_df.reset_index()
                
                # Rename columns for clarity
                pivot_df = pivot_df.rename(columns={
                    "OLD_Status": "Status (OLD)",
                    "NEW_Status": "Status (NEW)",
                    "OLD_Hiring Manager": "Hiring Manager (OLD)",
                    "NEW_Hiring Manager": "Hiring Manager (NEW)"
                })
                
                # Add status change indicator
                pivot_df["Status Changed?"] = pivot_df.apply(
                    lambda row: "Yes" if str(row.get("Status (OLD)", "")).lower() != str(row.get("Status (NEW)", "")).lower() 
                    and pd.notna(row.get("Status (OLD)")) and pd.notna(row.get("Status (NEW)"))
                    else "No",
                    axis=1
                )

            # ---------- DISPLAY RESULTS ----------
            st.subheader("📋 Active Status Records from Both Files")

            # Create tabs for different views
            tab_combined, tab_old, tab_new, tab_comparison, tab_hm_analysis = st.tabs([
                "📄 Combined View",
                "📁 OLD File Only",
                "📁 NEW File Only",
                "🔄 Comparison View",
                "👥 Hiring Manager Analysis"
            ])

            with tab_combined:
                st.write("**All Active Status Records (OLD + NEW):**")
                st.dataframe(final_download_df, use_container_width=True)
                
                # Show statistics
                st.write("**Statistics by Source:**")
                source_stats = final_download_df.groupby(["Source", "Status"]).size().unstack(fill_value=0)
                st.dataframe(source_stats, use_container_width=True)

            with tab_old:
                if not old_active.empty:
                    st.write(f"**Active Statuses from OLD File ({len(old_active)} records):**")
                    old_display = old_active.copy()
                    old_display["Status"] = old_display["Status"].str.title()
                    st.dataframe(old_display, use_container_width=True)
                else:
                    st.info("No active status records found in OLD file")

            with tab_new:
                if not new_active.empty:
                    st.write(f"**Active Statuses from NEW File ({len(new_active)} records):**")
                    new_display = new_active.copy()
                    new_display["Status"] = new_display["Status"].str.title()
                    st.dataframe(new_display, use_container_width=True)
                else:
                    st.info("No active status records found in NEW file")

            with tab_comparison:
                if 'pivot_df' in locals() and not pivot_df.empty:
                    st.write("**Side-by-Side Comparison:**")
                    st.dataframe(pivot_df, use_container_width=True)
                    
                    # Show comparison statistics
                    if "Status Changed?" in pivot_df.columns:
                        changed_count = pivot_df["Status Changed?"].eq("Yes").sum()
                        st.metric("Status Changed Records", changed_count)
                else:
                    st.info("Comparison view requires data in both files")

            with tab_hm_analysis:
                st.subheader("👥 Hiring Manager Analysis")
                
                # ---------- HIRING MANAGER FILTER ----------
                # Get all unique hiring managers
                all_hiring_managers = []
                for df in [old_active, new_active]:
                    if "Hiring Manager" in df.columns:
                        # Clean hiring manager names
                        df["Hiring Manager"] = df["Hiring Manager"].astype(str).str.strip()
                        hm_list = df["Hiring Manager"].dropna().unique().tolist()
                        all_hiring_managers.extend(hm_list)
                
                # Remove empty strings and get unique values
                all_hiring_managers = [hm for hm in all_hiring_managers if hm and hm not in ["nan", "None", "null", ""]]
                all_hiring_managers = sorted(list(set(all_hiring_managers)))
                
                if all_hiring_managers:
                    # Filter section
                    col_filter1, col_filter2 = st.columns([2, 1])
                    
                    with col_filter1:
                        selected_hiring_manager = st.selectbox(
                            "🔍 Select Hiring Manager to Filter:",
                            options=["All Hiring Managers"] + all_hiring_managers,
                            index=0
                        )
                    
                    with col_filter2:
                        show_source = st.selectbox(
                            "Show Data from:",
                            options=["Both Files", "OLD File Only", "NEW File Only"]
                        )
                    
                    # ---------- HIRING MANAGER STATISTICS ----------
                    st.write("### 📊 Hiring Manager Statistics")
                    
                    # Calculate request counts per hiring manager
                    hm_stats_data = []
                    
                    # For OLD file
                    if not old_active.empty and "Hiring Manager" in old_active.columns:
                        old_hm_counts = old_active.groupby("Hiring Manager")["Request ID"].nunique().reset_index()
                        old_hm_counts.columns = ["Hiring Manager", "Request Count (OLD)"]
                        hm_stats_data.append(old_hm_counts)
                    
                    # For NEW file
                    if not new_active.empty and "Hiring Manager" in new_active.columns:
                        new_hm_counts = new_active.groupby("Hiring Manager")["Request ID"].nunique().reset_index()
                        new_hm_counts.columns = ["Hiring Manager", "Request Count (NEW)"]
                        hm_stats_data.append(new_hm_counts)
                    
                    # Merge statistics
                    if hm_stats_data:
                        hm_stats = hm_stats_data[0]
                        for df in hm_stats_data[1:]:
                            hm_stats = pd.merge(hm_stats, df, on="Hiring Manager", how="outer")
                        
                        # Fill NaN with 0
                        hm_stats = hm_stats.fillna(0)
                        
                        # Calculate total requests
                        count_cols = [col for col in hm_stats.columns if "Request Count" in col]
                        hm_stats["Total Requests"] = hm_stats[count_cols].sum(axis=1)
                        
                        # Sort by total requests (descending)
                        hm_stats = hm_stats.sort_values("Total Requests", ascending=False)
                        
                        # Display hiring manager statistics
                        st.dataframe(hm_stats, use_container_width=True)
                        
                        # ---------- FILTERED VIEW ----------
                        st.write("### 📋 Filtered Records")
                        
                        # Apply filters
                        filtered_data = final_download_df.copy()
                        
                        # Filter by hiring manager
                        if selected_hiring_manager != "All Hiring Managers":
                            filtered_data = filtered_data[filtered_data["Hiring Manager"] == selected_hiring_manager]
                        
                        # Filter by source
                        if show_source == "OLD File Only":
                            filtered_data = filtered_data[filtered_data["Source"] == "OLD"]
                        elif show_source == "NEW File Only":
                            filtered_data = filtered_data[filtered_data["Source"] == "NEW"]
                        
                        if not filtered_data.empty:
                            # Show filtered data
                            st.write(f"**Showing {len(filtered_data)} records for {selected_hiring_manager if selected_hiring_manager != 'All Hiring Managers' else 'all hiring managers'}**")
                            st.dataframe(filtered_data, use_container_width=True)
                            
                            # Show breakdown by status
                            st.write("**Status Distribution:**")
                            status_dist = filtered_data.groupby("Status").size().reset_index(name="Count")
                            status_dist = status_dist.sort_values("Count", ascending=False)
                            
                            col_chart1, col_chart2 = st.columns(2)
                            
                            with col_chart1:
                                st.dataframe(status_dist, use_container_width=True)
                            
                            with col_chart2:
                                # Create a simple bar chart
                                if not status_dist.empty:
                                    fig, ax = plt.subplots()
                                    bars = ax.bar(status_dist["Status"], status_dist["Count"])
                                    ax.set_xlabel("Status")
                                    ax.set_ylabel("Count")
                                    ax.set_title(f"Requests by Status\n{selected_hiring_manager if selected_hiring_manager != 'All Hiring Managers' else 'All Hiring Managers'}")
                                    ax.tick_params(axis='x', rotation=45)
                                    
                                    # Add count labels on bars
                                    for bar in bars:
                                        height = bar.get_height()
                                        ax.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                                                f'{int(height)}', ha='center', va='bottom')
                                    
                                    st.pyplot(fig)
                            
                            # Show detailed breakdown by source and status
                            st.write("**Detailed Breakdown:**")
                            detailed_stats = filtered_data.groupby(["Source", "Status"]).size().unstack(fill_value=0)
                            st.dataframe(detailed_stats, use_container_width=True)
                            
                            # Download filtered data
                            st.download_button(
                                f"⬇️ Download Filtered Data ({len(filtered_data)} records)",
                                data=to_excel(filtered_data),
                                file_name=f"filtered_active_statuses_{selected_hiring_manager.lower().replace(' ', '_') if selected_hiring_manager != 'All Hiring Managers' else 'all'}.xlsx",
                                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                            )
                        else:
                            st.info("No records found with the selected filters.")
                    
                    else:
                        st.info("No Hiring Manager data available in the files.")
                else:
                    st.warning("⚠️ No Hiring Manager data found in the files.")

            # ---------- DOWNLOAD OPTIONS ----------
            st.subheader("📥 Download Active Status Records")

            col_dl1, col_dl2, col_dl3 = st.columns(3)

            with col_dl1:
                # Download COMBINED data (Active statuses from both files)
                st.download_button(
                    "⬇️ Download ALL Active Statuses",
                    data=to_excel(final_download_df),
                    file_name="active_statuses_from_both_files.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Contains Active, Partially Filled, Zero Filled from BOTH OLD and NEW files"
                )

            with col_dl2:
                # Download OLD file active statuses
                if not old_active.empty:
                    old_active_download = old_active.copy()
                    old_active_download["Status"] = old_active_download["Status"].str.title()
                    st.download_button(
                        "⬇️ Download OLD File Active",
                        data=to_excel(old_active_download),
                        file_name="active_statuses_old_file.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("No OLD file data")

            with col_dl3:
                # Download NEW file active statuses
                if not new_active.empty:
                    new_active_download = new_active.copy()
                    new_active_download["Status"] = new_active_download["Status"].str.title()
                    st.download_button(
                        "⬇️ Download NEW File Active",
                        data=to_excel(new_active_download),
                        file_name="active_statuses_new_file.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
                else:
                    st.info("No NEW file data")

            # ---------- ADDITIONAL DOWNLOAD OPTIONS ----------
            if 'pivot_df' in locals() and not pivot_df.empty:
                st.download_button(
                    "⬇️ Download Comparison View",
                    data=to_excel(pivot_df),
                    file_name="active_status_comparison.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    help="Side-by-side comparison of OLD vs NEW"
                )

            # ---------- STATUS BREAKDOWN ----------
            st.subheader("📊 Status Distribution")
            
            if not final_download_df.empty:
                # Create metrics for each status type
                status_counts = final_download_df["Status"].value_counts()
                
                cols = st.columns(len(status_counts))
                for idx, (status, count) in enumerate(status_counts.items()):
                    with cols[idx]:
                        if "Active" in status:
                            st.metric(f"🟢 {status}", count)
                        elif "Partially" in status:
                            st.metric(f"🟡 {status}", count)
                        elif "Zero" in status:
                            st.metric(f"🔵 {status}", count)
                
                # Show source breakdown
                st.write("**Breakdown by File Source:**")
                source_status = final_download_df.groupby(["Source", "Status"]).size().unstack(fill_value=0)
                st.dataframe(source_status, use_container_width=True)

            st.success(f"✅ Extracted {len(final_download_df)} active status records from both files")