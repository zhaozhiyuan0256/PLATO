import sys
import copy
import math
import ephem
from astropy.time import Time
import networkx as nx
import numpy as np
from skyfield.api import EarthSatellite, load
import datetime


def compute_paths_from_tles(tles_filepath, time_str, out_filepath):
    epoch = Time("2000-01-01 00:00:00", scale="tdb")
    graph = nx.Graph()
    num_orbits = 0
    num_sat_per_orbit = 0
    num_satellites = 0
    satellite_list = []
    neighbour_matrix = []

    # Initialize Topology
    starttime = datetime.datetime.now()

    with open(tles_filepath, "r") as f_tle:
        firstline = f_tle.readline().strip().split()
        num_orbits, num_sat_per_orbit = int(firstline[0]), int(firstline[1])
        num_satellites = num_orbits * num_sat_per_orbit
        for row in f_tle:
            row = row.strip()
            line1 = f_tle.readline().strip()
            line2 = f_tle.readline().strip()
            cur_satellite = ephem.readtle(row, line1, line2)
            satellite_list.append(cur_satellite)

    graph.add_nodes_from([i for i in range(num_satellites)])
    neighbour_matrix = [[] for i in range(num_satellites)]


    for i in range(num_orbits):
        for j in range(num_sat_per_orbit):
            cur_satellite_index = i * num_sat_per_orbit + j
            next_sat_in_same_orbit_index = (
                i * num_sat_per_orbit + (j + 1) % num_sat_per_orbit
            )
            next_sat_in_adjacent_orbit_index = (
                i + 1
            ) % num_orbits * num_sat_per_orbit + j
            cur_satellite = satellite_list[cur_satellite_index]
            next_sat_in_same_orbit = satellite_list[next_sat_in_same_orbit_index]
            next_sat_in_adjacent_orbit = satellite_list[
                next_sat_in_adjacent_orbit_index
            ]
            distance_between_sat_in_same_orbit = distance_m_between_satellites(
                cur_satellite, next_sat_in_same_orbit, str(epoch), str(time_str)
            )
            distance_between_sat_in_adjacent_orbit = distance_m_between_satellites(
                cur_satellite,
                next_sat_in_adjacent_orbit,
                str(epoch),
                str(time_str),
            )
            graph.add_edge(
                cur_satellite_index,
                next_sat_in_same_orbit_index,
                distance=distance_between_sat_in_same_orbit,
            )
            graph.add_edge(
                cur_satellite_index,
                next_sat_in_adjacent_orbit_index,
                distance=distance_between_sat_in_adjacent_orbit,
            )
            neighbour_matrix[cur_satellite_index].append(next_sat_in_same_orbit_index)
            neighbour_matrix[cur_satellite_index].append(
                next_sat_in_adjacent_orbit_index
            )
            neighbour_matrix[next_sat_in_same_orbit_index].append(cur_satellite_index)
            neighbour_matrix[next_sat_in_adjacent_orbit_index].append(
                cur_satellite_index
            )
    endtime = datetime.datetime.now()
    print(
        "Initialize Topology Time: ",
        (endtime - starttime).total_seconds(),
        "s",
    )

    # Calculate all sat-pair distance
    starttime = datetime.datetime.now()

    distance = nx.floyd_warshall_numpy(graph, weight="distance").tolist()

    endtime = datetime.datetime.now()
    print(
        "Floyd Calculation Distance Matrix Time: ",
        (endtime - starttime).total_seconds(),
        "s",
    )

    # with open("./a.txt", "w") as fff:
    #     for i in range(num_satellites):
    #         for j in range(num_satellites):
    #             print(distance[i][j], end=" ", file=fff)
    #         print(file=fff)

    # Calculate Paths by distance matrix
    starttime = datetime.datetime.now()
    f_out = open(out_filepath, "w")
    flag = 0

    # maxdistance = 0
    # for i in range(num_satellites):
    #     for j in range(num_satellites):
    #         maxdistance = max(maxdistance, distance[i][j])
    # print(maxdistance)
    # 36354865.0

    predecessor = [[-1 for i in range(num_satellites)] for j in range(num_satellites)]
    for i in range(num_satellites):
        for j in range(num_satellites):
            flag = 0
            if i != j:  # & (j not in neighbour_matrix[i]):
                # print(i,j,self.__neighbour_matrix[i])
                for neighbour in neighbour_matrix[i]:
                    if (
                        distance[i][neighbour] + distance[neighbour][j]
                        == distance[i][j]
                    ):
                        # min_cost = graph[i][neighbour] + graph[neighbour][j]
                        # print(i,j,neighbour,parents[i][j], parents[neighbour][j])
                        predecessor[i][j] = neighbour
                        # flag = 1
                        break
                # if flag!=1 :
                #     print("error",i,j,distance[i][neighbour],distance[neighbour][j],distance[i][j])
    endtime = datetime.datetime.now()
    print(
        "Predecessor Matrix Update Time: ",
        (endtime - starttime).total_seconds(),
        "s",
    )

    with open("./aa.txt", "w") as fff:
        for i in range(num_satellites):
            for j in range(num_satellites):
                print(predecessor[i][j], end=" ", file=fff)
            print(file=fff)


    # Write paths to file
    # starttime = datetime.datetime.now()
    # f_out = open(out_filepath, "w+")
    # print(num_satellites)
    # for i in range(num_satellites):
    #     for j in range(num_satellites):
    #         if i == j:
    #             break
    #         print("Path({}-->{}): ".format(i, j), end="", file=f_out, flush=False)
    #         now = i
    #         print("{} -->".format(now), end="", file=f_out, flush=False)
    #         while True:
    #             now = predecessor[now][j]
    #             if now == j:
    #                 print(j, end="", file=f_out, flush=False)
    #                 break
    #             else:
    #                 print("{} -->".format(now), end="", file=f_out, flush=False)

    #         # print_path(i, j, j, outfile=f_out)
    #         print(
    #             " cost: {}".format(distance[i][j]),
    #             file=f_out,
    #             flush=False,
    #         )
    # endtime = datetime.datetime.now()
    # print(
    #     out_filepath,
    #     "File Write Time: ",
    #     (endtime - starttime).total_seconds(),
    #     "s",
    # )
    # starttime = datetime.datetime.now()

    # predecessor, distance = nx.floyd_warshall_predecessor_and_distance(graph,weight="distance")
    # # print(distance)
    # # print(predecessor)
    # endtime = datetime.datetime.now()
    # print(
    #     " Update Time: ",
    #     (endtime - starttime).total_seconds(),
    #     "s",
    # )

    # for i in range(num_satellites):
    #     for j in range(num_satellites):
    #         path = nx.shortest_path(graph, i, j, weight="distance")
    #         length = nx.shortest_path_length(graph, i, j, weight="distance")
    #         print("Path({}-->{}): ".format(i, j), end="", file=f_out)
    #         for k in range(len(path)):
    #             print(path[k], end="", file=f_out)
    #             if k != len(path) - 1:
    #                 print("-->", end="", file=f_out)
    #         print(
    #             " cost: {}".format(length),
    #             file=f_out,
    #             flush=False,
    #         )
    #


def distance_m_between_satellites(sat1, sat2, epoch_str, date_str):
    """
    Computes the straight distance between two satellites in meters.

    :param sat1:       The first satellite
    :param sat2:       The other satellite
    :param epoch_str:  Epoch time of the observer (string)
    :param date_str:   The time instant when the distance should be measured (string)

    :return: The distance between the satellites in meters
    """

    # Create an observer somewhere on the planet
    observer = ephem.Observer()
    observer.epoch = epoch_str
    observer.date = date_str
    observer.lat = 0
    observer.lon = 0
    observer.elevation = 0

    # Calculate the relative location of the satellites to this observer
    sat1.compute(observer)
    sat2.compute(observer)

    # Calculate the angle observed by the observer to the satellites (this is done because the .compute() calls earlier)
    angle_radians = float(repr(ephem.separation(sat1, sat2)))

    return int(
        math.sqrt(
            sat1.range**2
            + sat2.range**2
            - (2 * sat1.range * sat2.range * math.cos(angle_radians))
        )
    )


if __name__ == "__main__":

    # tles_filepath = "./TLE/demo_16x16_tle.txt"
    # time_str = "2000-01-01 00:01:00"
    # compute_paths_from_tles(tles_filepath, time_str, "PATH/demo_16x16_tle.txt")

    tles_filepath = "./TLE/starlink_tle.txt"
    time_str = "2000-01-01 00:01:00"
    compute_paths_from_tles(tles_filepath, time_str, "PATH/starlink_tle.txt")
    # Initialize Topology Time:  0.047977 s
    # Floyd Calculation Distance Matrix Time:  8.247252 s
    # Predecessor Matrix Update Time:  0.619295 s
