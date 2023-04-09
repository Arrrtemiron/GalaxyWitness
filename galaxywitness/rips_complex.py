import gudhi
from gudhi.clustering.tomato import Tomato

import matplotlib.pyplot as plt
import plotly.graph_objects as go
import numpy as np

from galaxywitness.base_complex import BaseComplex

# hard-coded
MAX_N_PLOT = 10000
NUMBER_OF_FRAMES = 6


class RipsComplex(BaseComplex):
    """
    Main class for handling data about the point cloud and the simplex tree
    of filtered rips complex

    :param points: set of landmarks in :math:`\mathbb{R}^d`.
    :type points: np.array size of *n_landmarks x 3*

    """

    def __init__(self, points, max_edge_length, sparse=None):
        """
        Constuctor

        """
        super().__init__(points)
        self.max_edge_length = max_edge_length
        self.sparse = sparse
        self.max_dimension = 1  # default value though can be changed

    def compute_simplicial_complex(self, r_max, **kwargs):
        """
        Compute custom filtered simplicial complex

        :param r_max: max filtration value
        :type  r_max: float

        """

        tmp = gudhi.RipsComplex(points=self.points, max_edge_length=self.max_edge_length, sparse=self.sparse)

        self.simplex_tree = tmp.create_simplex_tree(max_dimension=self.max_dimension)
        self.simplex_tree_computed = True

    def animate_simplex_tree(self, path_to_save):
        """
        Draw animation of filtration (powered by matplotlib)

        :param path_to_save: place, where we are saving files
        :type  path_to_save: str

        """
        assert self.simplex_tree_computed

        gen = self.simplex_tree.get_filtration()
        data = []
        gen = list(gen)
        scale = NUMBER_OF_FRAMES / gen[-1][1]

        for num in range(1, NUMBER_OF_FRAMES + 1):
            fig = plt.figure()
            ax = fig.add_subplot(projection="3d")

            ax.scatter3D(self.points[:MAX_N_PLOT, 0],
                         self.points[:MAX_N_PLOT, 1],
                         self.points[:MAX_N_PLOT, 2],
                         s=2,
                         linewidths=1,
                         color='C1')

            ax.set_xlabel('X, Mpc')
            ax.set_ylabel('Y, Mpc')
            ax.set_zlabel('Z, Mpc')

            super().draw_simplicial_complex(ax, data, num / scale)

            ax.set_title(f"Animation of rips filtration: picture #{num} of {NUMBER_OF_FRAMES}")

            if path_to_save is not None:
                plt.savefig(path_to_save + f"/picture{num}.png", dpi=200)

            plt.show()

    def animate_simplex_tree_plotly(self, path_to_save):
        """
        Draw animation of filtration (powered by plotly)

        :param path_to_save: place, where we are saving files
        :type  path_to_save: str
        """
        assert self.simplex_tree_computed

        gen = self.simplex_tree.get_filtration()

        gen = list(gen)
        scale = NUMBER_OF_FRAMES / gen[-1][1]

        for num in range(1, NUMBER_OF_FRAMES + 1):
            fig = plt.figure()
            ax = fig.add_subplot(projection="3d")

            data = []

            super().draw_simplicial_complex(ax, data, num / scale)

            fig = go.Figure(data=data)

            fig.update_layout(scene=dict(xaxis_title="X, Mpc",
                                         yaxis_title="Y, Mpc",
                                         zaxis_title="Z, Mpc"))

            if path_to_save is not None:
                fig.write_image(path_to_save + f"/picture{num}.pdf")

            fig.show()

    def get_adjacency_list(self):
        rips_complex = gudhi.RipsComplex(self.points, max_edge_length=self.max_edge_length, sparse=self.sparse)
        simplex_tree = rips_complex.create_simplex_tree()

        adjacency_list = simplex_tree.get_skeleton(1)
        tmp = []
        for i in range(len(self.points)):
            tmp.append(set())
        for elem in adjacency_list:
            if len(elem[0]) == 1:
                continue
            tmp[elem[0][0]].add(elem[0][1])
            tmp[elem[0][1]].add(elem[0][0])

        adjacency_list = []
        for elem in tmp:
            adjacency_list.append(list(elem))

        return adjacency_list

    def tomato(self, den_type, graph):
        """
        ToMATo clustering with automatic choice of number of clusters.
        Hence, clustering depends on filtered complex construction and
        max value of filtration.

        """
        self.graph_type = graph
        t = Tomato(density_type=den_type, graph_type=self.graph_type)
        if den_type == 'manual' and self.graph_type != 'manual':
            t.fit(self.points, weights=self.density_class.foo(self.points))
        elif den_type == 'manual' and self.graph_type == 'manual':
            t.fit(self.get_adjacency_list(), weights=self.density_class.foo(self.points))
        else:
            t.fit(self.points)
        t.n_clusters_ = self.betti[0]
        return t
