#!/usr/bin/env python
# ----------------------------------
# @author: ZuyuanZhu
# @email: zuyuanzhu@gmail.com
# @date: 20 Apr 2021
# ----------------------------------


import topological_simpy.visualise
import random
import os
from datetime import datetime
import matplotlib.pyplot
import numpy
import pandas
import seaborn
import rospy


class VisualiseAgentsSim(topological_simpy.visualise.VisualiseAgents):
    """
    A class to animate agent locations in matplotlib
    This extension class updates to match topological map2 format.
    """

    def __init__(self, log_dir, topo_graph, robots, pickers, policy, n_deadlock, tmap_name, show_cs=False, save_random=False,
                 save_final=False, trial=0):

        super(VisualiseAgentsSim, self).__init__(topo_graph, robots, pickers, policy, show_cs=False,
                                                 save_random=False, trial=0)
        self.show_cold_storage = show_cs  # should the cold storage be shown
        self.save_fig = save_random
        self.trial = trial

        self.show_cbar = True
        self.save_final_fig = save_final
        self.log_dir = log_dir

        self.heatmap_values = None
        self.heatmap_index_max_x = None
        self.heatmap_index_min_x = None
        self.heatmap_index_min_y = None
        self.heatmap_index_max_y = None
        self.heatmap_node_pose_x_list = None
        self.heatmap_node_pose_y_list = None
        self.tmap_name = tmap_name
        self.n_deadlock = n_deadlock

        self.fig_name_base = self.log_dir + "/P%d_R%d_S%s_T%d_" % (
            self.n_pickers, self.n_robots, self.policy, self.trial)

        self.f_handle = open(self.fig_name_base + datetime.now().isoformat().replace(":", "_") + "_heatmap.yaml", "w")

    def init_plot(self):
        """Initialise the plot frame"""
        farm_rows_x, farm_rows_y = [], []
        nav_rows_x, nav_rows_y = [], []
        nav_row_nodes_x, nav_row_nodes_y = [], []
        pri_head_lane_x, pri_head_lane_y = [], []
        pri_head_nodes_x, pri_head_nodes_y = [], []
        if self.graph.second_head_lane:
            sec_head_lane_x, sec_head_lane_y = [], []
            sec_head_nodes_x, sec_head_nodes_y = [], []
        local_storage_x, local_storage_y = [], []
        local_storage_nodes = []
        cold_storage_node = None

        for i in range(self.graph.n_topo_nav_rows):
            row_id = self.graph.row_ids[i]
            pri_head_node = self.graph.get_node(self.graph.head_nodes[row_id][0])
            pri_head_nodes_x.append(pri_head_node['node']['pose']['position']['x'])
            pri_head_nodes_y.append(pri_head_node['node']['pose']['position']['y'])
            if self.graph.second_head_lane:
                sec_head_node = self.graph.get_node(self.graph.head_nodes[row_id][1])
                sec_head_nodes_x.append(sec_head_node['node']['pose']['position']['x'])
                sec_head_nodes_y.append(sec_head_node['node']['pose']['position']['y'])
            for j in range(len(self.graph.row_nodes[row_id])):
                curr_node = self.graph.get_node(self.graph.row_nodes[row_id][j])
                if j == 0:
                    start_node = curr_node
                elif j == len(self.graph.row_nodes[row_id]) - 1:
                    last_node = curr_node
                nav_row_nodes_x.append(curr_node['node']['pose']['position']['x'])
                nav_row_nodes_y.append(curr_node['node']['pose']['position']['y'])

            if self.graph.second_head_lane:
                # from head_node to last_row_node of the row
                nav_rows_x.append(
                    (pri_head_node['node']['pose']['position']['x'], sec_head_node['node']['pose']['position']['x']))
                nav_rows_y.append(
                    (pri_head_node['node']['pose']['position']['y'], sec_head_node['node']['pose']['position']['y']))
            else:
                # from head_node to last_row_node of the row
                nav_rows_x.append(
                    (pri_head_node['node']['pose']['position']['x'], last_node['node']['pose']['position']['x']))
                nav_rows_y.append(
                    (pri_head_node['node']['pose']['position']['y'], last_node['node']['pose']['position']['y']))

            # primary head lane
            #            if (i == 0) or (i == self.graph.n_topo_nav_rows - 1):
            pri_head_lane_x.append(pri_head_node['node']['pose']['position']['x'])
            pri_head_lane_y.append(pri_head_node['node']['pose']['position']['y'])

            # secondary head lane
            if self.graph.second_head_lane:
                #                if (i == 0) or (i == self.graph.n_topo_nav_rows - 1):
                sec_head_lane_x.append(sec_head_node['node']['pose']['position']['x'])
                sec_head_lane_y.append(sec_head_node['node']['pose']['position']['y'])

            # farm rows
            if i < self.graph.n_topo_nav_rows - 1:
                curr_row_id = self.graph.row_ids[i]
                next_row_id = self.graph.row_ids[i + 1]
                if not (curr_row_id in self.graph.half_rows and next_row_id in self.graph.half_rows):
                    curr_row_start_node = self.graph.get_node(self.graph.row_nodes[curr_row_id][0])
                    curr_row_last_node = self.graph.get_node(self.graph.row_nodes[curr_row_id][-1])
                    next_row_start_node = self.graph.get_node(self.graph.row_nodes[next_row_id][0])
                    next_row_last_node = self.graph.get_node(self.graph.row_nodes[next_row_id][-1])
                    start_node_x = curr_row_start_node['node']['pose']['position']['x'] + 0.5 * (
                            next_row_start_node['node']['pose']['position']['x'] -
                            curr_row_start_node['node']['pose']['position']['x'])
                    start_node_y = curr_row_start_node['node']['pose']['position']['y'] + 0.5 * (
                            next_row_start_node['node']['pose']['position']['y'] -
                            curr_row_start_node['node']['pose']['position']['y'])
                    last_node_x = curr_row_last_node['node']['pose']['position']['x'] + 0.5 * (
                            next_row_last_node['node']['pose']['position']['x'] -
                            curr_row_last_node['node']['pose']['position']['x'])
                    last_node_y = curr_row_last_node['node']['pose']['position']['y'] + 0.5 * (
                            next_row_last_node['node']['pose']['position']['y'] -
                            curr_row_last_node['node']['pose']['position']['y'])

                    farm_rows_x.append((start_node_x, last_node_x))
                    farm_rows_y.append((start_node_y, last_node_y))

            if self.graph.local_storage_nodes[row_id] not in local_storage_nodes:
                local_storage_nodes.append(self.graph.local_storage_nodes[row_id])
                node_obj = self.graph.get_node(local_storage_nodes[-1])
                local_storage_x.append(node_obj['node']['pose']['position']['x'])
                local_storage_y.append(node_obj['node']['pose']['position']['y'])

            if self.graph.cold_storage_node is not None:
                cold_storage_node = self.graph.cold_storage_node
                node_obj = self.graph.get_node(cold_storage_node)
                cold_storage_x = node_obj['node']['pose']['position']['x']
                cold_storage_y = node_obj['node']['pose']['position']['y']

        if not self.show_cold_storage:
            min_x = min(min(nav_rows_x[0]), min(farm_rows_x[0]))
            max_x = max(max(nav_rows_x[-1]), max(farm_rows_x[-1]))
            min_y = min(min(nav_rows_y[0]), min(farm_rows_y[0]))
            max_y = max(max(nav_rows_y[-1]), max(farm_rows_y[-1]))

            # limits of the axes
            self.ax[0].set_xlim(min_x - 5, max_x + 2.5)
            self.ax[0].set_ylim(min_y - 2.5, max_y + 7.5)

            # self.ax[1].set_xlim(min_x - 20, max_x + 50)
            # self.ax[1].set_ylim(min_y + 33, max_y)

        else:
            min_x = min(min(nav_rows_x[0]), min(farm_rows_x[0]), cold_storage_x)
            max_x = max(max(nav_rows_x[-1]), max(farm_rows_x[-1]), cold_storage_x)
            min_y = min(min(nav_rows_y[0]), min(farm_rows_y[0]), cold_storage_y)
            max_y = max(max(nav_rows_y[-1]), max(farm_rows_y[-1]), cold_storage_y)

            # limits of the axes
            self.ax[0].set_xlim(min_x - 15, max_x + 15)
            self.ax[0].set_ylim(min_y - 15, max_y + 15)

            # self.ax[1].set_xlim(min_x - 5, max_x + 5)
            # self.ax[1].set_ylim(min_y - 5, max_y + 5)

            # self.fig.set_figheight((max_y - min_y + 2)*2)
            # self.fig.set_figwidth((max_x - min_x + 2)*2)

        # static objects - nodes
        # nav_rows
        for i, item in enumerate(zip(nav_rows_x, nav_rows_y)):
            self.static_lines.append(self.ax[0].plot(item[0], item[1],
                                                     color="black", linewidth=4)[0])
        # farm_rows
        for i, item in enumerate(zip(farm_rows_x, farm_rows_y)):
            self.static_lines.append(self.ax[0].plot(item[0], item[1],
                                                     color="green", linewidth=4)[0])
        # primary head lane
        self.static_lines.append(self.ax[0].plot(pri_head_lane_x, pri_head_lane_y,
                                                 color="black", linewidth=4)[0])
        # secondary head lane
        if self.graph.second_head_lane:
            self.static_lines.append(self.ax[0].plot(sec_head_lane_x, sec_head_lane_y,
                                                     color="black", linewidth=4)[0])
        # nav_row_nodes
        self.static_lines.append(self.ax[0].plot(nav_row_nodes_x, nav_row_nodes_y,
                                                 color="black", marker="o", markersize=6,
                                                 linestyle="none")[0])
        # pri_head_lane_nodes
        self.static_lines.append(self.ax[0].plot(pri_head_nodes_x, pri_head_nodes_y,
                                                 color="black", marker="o", markersize=6,
                                                 linestyle="none")[0])
        # sec_head_lane_nodes
        if self.graph.second_head_lane:
            self.static_lines.append(self.ax[0].plot(sec_head_nodes_x, sec_head_nodes_y,
                                                     color="black", marker="o", markersize=6,
                                                     linestyle="none")[0])
        # local storages
        self.static_lines.append(self.ax[0].plot(local_storage_x, local_storage_y,
                                                 color="black", marker="s", markersize=12,
                                                 markeredgecolor="r", linestyle="none")[0])
        # cold_storage
        if self.show_cold_storage and cold_storage_node is not None:
            self.static_lines.append(self.ax[0].plot(cold_storage_x, cold_storage_y,
                                                     color="black", marker="8", markersize=12,
                                                     markeredgecolor="r", linestyle="none")[0])
            self.static_lines.append(self.ax[0].plot([pri_head_nodes_x[0], cold_storage_x],
                                                     [pri_head_nodes_y[0], cold_storage_y],
                                                     color="black", linewidth=4)[0])

        # dynamic objects - pickers and robots
        # pickers
        for i in range(self.n_pickers):
            picker = self.pickers[i]
            picker_id = picker.picker_id
            if picker.curr_node is not None:
                curr_node_obj = self.graph.get_node(picker.curr_node)
                x = curr_node_obj['node']['pose']['position']['x']
                y = curr_node_obj['node']['pose']['position']['y']
            else:
                x = y = 0.

            self.picker_position_lines.append(self.ax[0].plot(x, y,
                                                              color="b", marker="o",
                                                              markersize=20,
                                                              markeredgecolor="b",
                                                              linestyle="none")[0])
            self.picker_status_texts.append(self.ax[0].text(x - 2.9, y + 0.5,
                                                            "P_%s:%d" % (picker_id[-3:], picker.mode),
                                                            fontdict=self.font))
        # robots
        for i in range(self.n_robots):
            robot = self.robots[i]
            robot_id = robot.robot_id
            if robot.graph.curr_node[robot_id] is not None:
                curr_node_obj = self.graph.get_node(robot.graph.curr_node[robot_id])
                x = curr_node_obj['node']['pose']['position']['x']
                y = curr_node_obj['node']['pose']['position']['y']
            else:
                x = y = 0.

            self.robot_position_lines.append(self.ax[0].plot(x, y,
                                                             color="#8b12b3", marker="^",
                                                             markersize=20,
                                                             markeredgecolor="#8b12b3",
                                                             linestyle="none")[0])
            self.robot_status_texts.append(self.ax[0].text(x + 0.6, y + 0.5,
                                                           "R_%s:%d" % (robot_id, robot.mode),
                                                           fontdict=self.font))

        self.ax[0].tick_params(axis='x', labelsize=18)
        self.ax[0].tick_params(axis='y', labelsize=18)

        self.fig.canvas.draw()
        if self.save_fig:
            self.fig.savefig(
                self.fig_name_base + datetime.now().isoformat().replace(":", "_") + "_S_%.1f.eps" % self.graph.env.now)

        return (self.static_lines + self.picker_position_lines +
                self.picker_status_texts + self.robot_position_lines + self.robot_status_texts)

    def update_plot_bar(self):
        # plot the node resource usage
        valid_node_log = dict((k, v) for k, v in self.graph.node_log.iteritems() if v)
        names = list(valid_node_log.keys())
        values = [len(value) for value in valid_node_log.values()]
        self.ax[1].clear()
        self.ax[1].bar(range(len(names)), values, color='b')
        self.ax[1].set_xlabel('Topological node')
        self.ax[1].set_ylabel("Access times")
        self.ax[1].set_xticks(range(len(names)))
        self.ax[1].set_xticklabels(names, fontsize=9, rotation=45)

    def update_plot_heatmap(self):
        """
        Plot the heatmap of node usage
        """
        valid_node_log = dict((k, v) for k, v in self.graph.node_log.iteritems() if v)
        valid_node_log = dict((k, v) for k, v in self.graph.node_log.iteritems())   # take all nodes
        names = list(valid_node_log.keys())
        values = [len(value) for value in valid_node_log.values()]
        node_pose_x_list = []
        node_pose_y_list = []
        for node in names:
            node_obj = self.graph.get_node(node)
            node_pose_x_list.append(int(round(node_obj['node']['pose']['position']['x'])))  # meter to centimeter
            node_pose_y_list.append(int(round(node_obj['node']['pose']['position']['y'])))

        node_pose_x = numpy.array(node_pose_x_list)
        node_pose_y = numpy.array(node_pose_y_list)

        max_x = max(node_pose_x_list)
        min_x = min(node_pose_x_list)
        max_y = max(node_pose_y_list)
        min_y = min(node_pose_y_list)
        data = numpy.zeros((max_x - min_x,
                            max_y - min_y))

        for i, x in enumerate(node_pose_x):
            for j, y in enumerate(node_pose_y):
                if i == j:
                    data[x - min_x - 1, y - min_y - 1] = values[i]
                    break

        df = pandas.DataFrame(data,
                              index=numpy.linspace(min_x, max_x - 1, max_x - min_x, dtype='int'),
                              columns=numpy.linspace(min_y, max_y - 1, max_y - min_y, dtype='int'))
        self.ax[1].clear()

        seaborn.set(font_scale=1.6)

        # only initialise color bar once, then don't update it anymore
        if self.show_cbar:
            # get sharp grid back by removing rasterized=True, and save fig as svg format
            self.ax[1] = seaborn.heatmap(df, cbar=True, rasterized=True)
            self.show_cbar = False
        else:
            # get sharp grid back by removing rasterized=True, and save fig as svg format
            self.ax[1] = seaborn.heatmap(df, cbar=False, rasterized=True)
        # matplotlib.rcParams.update({'font.size': 22})
        # self.ax[1].set(xlabel='Node pose y', ylabel='Node pose x')
        self.ax[1].set_xlabel('Node pose y', fontsize=20)
        self.ax[1].set_ylabel('Node pose x', fontsize=20)

        # save data for logs
        self.heatmap_values = values
        self.heatmap_index_max_x = max_x
        self.heatmap_index_min_x = min_x
        self.heatmap_index_min_y = min_y
        self.heatmap_index_max_y = max_y
        self.heatmap_node_pose_x_list = node_pose_x_list
        self.heatmap_node_pose_y_list = node_pose_y_list

        self.n_deadlock = self.graph.n_deadlock

    def update_plot(self):
        """update the positions of the dynamic objects"""
        for i in range(self.n_pickers):
            picker = self.pickers[i]
            if picker.curr_node is not None:
                curr_node_obj = self.graph.get_node(picker.curr_node)
                x = curr_node_obj['node']['pose']['position']['x']
                y = curr_node_obj['node']['pose']['position']['y']
            else:
                x = y = 0.

            self.picker_position_lines[i].set_data(x, y)
            self.picker_status_texts[i].set_text("P_%s:%d" % (picker.picker_id[-3:], picker.mode))
            self.picker_status_texts[i].set_position((x - 2.9, y + 0.5))

        for i in range(self.n_robots):
            robot = self.robots[i]
            robot_id = robot.robot_id
            if robot.graph.curr_node[robot_id] is not None:
                curr_node_obj = self.graph.get_node(robot.graph.curr_node[robot_id])
                x = curr_node_obj['node']['pose']['position']['x']
                y = curr_node_obj['node']['pose']['position']['y']
            else:
                x = y = 0.
            self.robot_position_lines[i].set_data(x, y)
            self.robot_status_texts[i].set_text("R_%s:%d" % (robot.robot_id, robot.mode))
            self.robot_status_texts[i].set_position((x + 1.0, y + 0.5))

        # plot the node resource usage
        # self.update_plot_bar()

        self.update_plot_heatmap()

        # display simulation time
        title_text = 'Up: Discrete Event Simulation for Picking and Transporting Task\n' \
                     'Down: Topological Map Node Usage\n' \
                     'Simulation Time: %.1f s' % self.graph.env.now
        self.fig.suptitle(title_text)

        self.fig.canvas.draw()

        if self.save_fig:
            if random.random() < 0.1:
                self.fig.savefig(self.fig_name_base + datetime.now().isoformat().replace(":",
                                                                                         "_") + "_S_%.1f.eps" % self.graph.env.now)

        return (self.static_lines + self.picker_position_lines + self.picker_status_texts +
                self.robot_position_lines + self.robot_status_texts)

    def close_plot(self):
        """close plot"""
        if self.save_final_fig:
            # save a full fig
            self.fig.savefig(self.fig_name_base + datetime.now().isoformat().replace(":", "_") + ".eps")

            # Save just the portion _inside_ the second axis's boundaries
            extent = self.ax[1].get_window_extent().transformed(self.fig.dpi_scale_trans.inverted())
            self.fig.savefig(self.fig_name_base + datetime.now().isoformat().replace(":", "_") + "_heatmap.eps",
                             bbox_inches=extent.expanded(1.22, 1.24))

        matplotlib.pyplot.close(self.fig)

        # heatmap details
        print >> self.f_handle, "# heatmap details"
        print >> self.f_handle, "map_name: %s" % self.tmap_name.replace('../maps/', '').replace('.', '_')
        print >> self.f_handle, "trial: %d" % self.trial
        print >> self.f_handle, "n_deadlock: %d" % self.n_deadlock
        print >> self.f_handle, "simulation_time: %0.1f" % self.graph.env.now
        print >> self.f_handle, "heatmap_values: %s" % self.heatmap_values
        print >> self.f_handle, "heatmap_node_pose_x_list: %s" % self.heatmap_node_pose_x_list
        print >> self.f_handle, "heatmap_node_pose_y_list: %s" % self.heatmap_node_pose_y_list

        self.f_handle.close()
