import streamlit as st
from plotly import express as ex

from plotly.graph_objects import Figure
from numpy import isnan


def timelines_statistics() -> None:
    workflows = [
        (r, w, len(st.session_state["results_repos"][r][w]["shas"]))
        for r, ws in st.session_state["results_repos"].items() 
        for w in ws.keys()
    ]
    
    taus = [
        float(w["trend"][0])
        for ws in st.session_state["results_repos"].values() 
        for w in ws.values()
    ]
    
    fig = ex.scatter(
        x=[w[2] for w in workflows],
        y=taus,
        hover_data={
            "repository": [w[0] for w in workflows],
            "workflow": [w[1] for w in workflows],
        }
    )
    
    fig = fig.update_yaxes(showgrid=False, zerolinecolor="#E6EAF1", range=[-1.1, 1.1])
    fig = fig.update_xaxes(showgrid=False, zerolinecolor="#E6EAF1", range=[0.5, max([w[2] for w in workflows])+2])
    fig = fig.update_layout(yaxis_title="value of τ", xaxis_title="# of commits")
    
    trend_title_container = st.container(horizontal=True)
    trend_title_container.write("##### Vulnerability Trends")
    _ = trend_title_container.text("", help="Select a point on the plot to see the complete history for that workflow")
    
    trend_container = st.container(horizontal=True)
    selected_workflow = trend_container.plotly_chart(
        figure_or_data=fig,
        theme=None,
        on_select="rerun",
        selection_mode="points",
    )
    
    if len(selected_workflow["selection"]["points"]) > 0:
        repo = selected_workflow["selection"]["points"][0]["customdata"][0]
        workflow = selected_workflow["selection"]["points"][0]["customdata"][1]
        
        values = st.session_state["results_repos"][repo][workflow]
        
        fig = Figure()
        
        ys = ["direct_vuln", "direct_dev_vuln", "direct_opt_vuln", "indirect_vuln"]
        colors = ["rgb(99,110,251)", "rgb(110, 251, 99)", "rgb(250, 164, 97)", "rgb(61, 58, 42)"]
        
        for i in range(len(ys)):
            fig = fig.add_scatter(
                x=values["dates"],
                y=values["dependencies"][ys[i]],
                name=ys[i],
                marker={"color":colors[i]},
                line_shape="hv",
                mode="lines+markers",
            )
            
        fig = fig.update_xaxes(showgrid=False, zerolinecolor="#E6EAF1")
        fig = fig.update_yaxes(showgrid=True, zerolinecolor="#E6EAF1")
        fig = fig.update_layout(hovermode="x unified", title=f"{repo}/{workflow}")
        
        _ = trend_container.plotly_chart(figure_or_data=fig, theme=None)


def timelines_plot(repo_name: str, workflows: dict[str, dict[str, str]]) -> None:
    st.write(f"##### {repo_name}")

    workflows_container = st.container(gap="medium")

    for workflow, values in workflows.items():
        trend_arrow = "="
        
        if not isnan(values['trend'][1]) and values['trend'][1] <= 0.1:
            if 0 < values['trend'][0] <= .5:
                trend_arrow = "▲"
            elif .5 < values['trend'][0] <= 1:
                trend_arrow = "⏫︎"
            elif -.5 <= values['trend'][0] < 0:
                trend_arrow = "▼"
            elif -1 <= values['trend'][0] < .5:
                trend_arrow = "⏬︎"
        
        workflow_plots = workflows_container.container(gap="small")
        workflow_name = workflow_plots.container(horizontal=True, horizontal_alignment="left", gap="medium")
        
        tau = values['trend'][0] if not isnan(values['trend'][0]) else 0.0
        p_value = values['trend'][1] if not isnan(values['trend'][1]) else 0.0
        
        _ = workflow_name.write(f"###### {workflow}")
        _ = workflow_name.text(f"Trend: {trend_arrow}", help=f"τ = {tau}, p-value = {p_value}")

        col1, col2 = workflow_plots.columns(2)

        fig1 = Figure()
        fig2 = Figure()

        ys = ["direct", "direct_dev", "direct_opt", "indirect"]
        colors = ["rgb(99,110,251)", "rgb(110, 251, 99)", "rgb(250, 164, 97)", "rgb(61, 58, 42)"]

        for i in range(len(ys)):
            fig1 = fig1.add_scatter(
                x=values["dates"],
                y=values["dependencies"][ys[i]],
                name=ys[i],
                marker={"color":colors[i]},
                line_shape="hv",
                mode="lines+markers",
            )
            
            fig2 = fig2.add_scatter(
                x=values["dates"],
                y=values["dependencies"][ys[i]+"_vuln"],
                name=ys[i],
                marker={"color":colors[i]},
                line_shape="hv",
                mode="lines+markers",
            )

        
        fig1 = fig1.update_xaxes(showgrid=False, zerolinecolor="#E6EAF1")
        fig1 = fig1.update_yaxes(showgrid=True, zerolinecolor="#E6EAF1")
        fig1 = fig1.update_layout(hovermode="x unified")
        
        fig2 = fig2.update_xaxes(showgrid=False, zerolinecolor="#E6EAF1")
        fig2 = fig2.update_yaxes(showgrid=True, zerolinecolor="#E6EAF1")
        fig2 = fig2.update_layout(hovermode="x unified")

        _ = col1.plotly_chart(figure_or_data=fig1, theme=None, key=f"{repo_name}-{workflow}-acol1", on_select="rerun")
        _ = col2.plotly_chart(figure_or_data=fig2, theme=None, key=f"{repo_name}-{workflow}-acol2", on_select="rerun")
