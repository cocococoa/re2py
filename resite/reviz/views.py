from django.shortcuts import render
from graphviz.jupyter_integration import SVG_ENCODING
from re2py import re2post, post2nfa, match


def get_value_or(request, key, default):
    try:
        value = request.POST[key].strip()
    except Exception:
        value = ""
    if value == "":
        value = default
    return value


def emphasized_string(string: str, indexes):
    ret = ""
    for i, c in enumerate(string):
        if i in indexes:
            ret += f'<font color="red">{c}</font>'
        else:
            ret += c
    return ret


def index(request):
    context = {
        "regex": "",
        "string": "",
        "regex_compiled": False,
        "simulation_compiled": False,
        "svg": "",
        "svg_node_config": list(),
        "svg_list": list(),
        "exception": "",
    }

    try:
        # Parse POST info.
        regex = get_value_or(request, "regex", "")
        context["regex"] = regex
        string = get_value_or(request, "string", "")
        context["string"] = string

        nfa = None
        graph = None
        node_config = list()
        context["svg_node_config"] = node_config
        if regex != "":
            nfa = post2nfa(re2post(regex))
            graph = nfa.graph()

            for i in range(graph.number_of_nodes()):
                color_base = "black"
                shape_base = "oval"
                label_base = graph.get_label(i)

                color = get_value_or(
                    request, f"svg_node_config_color_{i+1}", color_base
                )
                shape = get_value_or(
                    request, f"svg_node_config_shape_{i+1}", shape_base
                )
                label = get_value_or(
                    request, f"svg_node_config_label_{i+1}", label_base
                )

                node_config.append(
                    {
                        "name": label_base,
                        "original_color": color != color_base,
                        "color": color,
                        "original_shape": shape != shape_base,
                        "shape": shape,
                        "original_label": label != label_base,
                        "label": label,
                    }
                )
            context["regex_compiled"] = True

        # Generate NFA's SVG
        if regex != "":
            graph.format = "svg"
            for i in range(graph.number_of_nodes()):
                config = node_config[i]
                graph.node(i, config["color"], config["shape"], config["label"])
            context["svg"] = graph.pipe("utf-8")

        # Generate NFA simulation's SVG
        svg_list = list()
        context["svg_list"] = svg_list
        if regex != "" and string != "":
            history = []
            is_matched = match(graph.nodes[graph.entry], string, history)
            for c, states in enumerate(history):
                for i in range(graph.number_of_nodes()):
                    config = node_config[i]
                    if i in states:
                        graph.node(
                            i,
                            config["color"],
                            config["shape"],
                            config["label"],
                            fillcolor="red",
                        )
                    else:
                        graph.node(i, config["color"], config["shape"], config["label"])
                svg_list.append(
                    {"tag": emphasized_string(string, [c]), "svg": graph.pipe("utf-8")}
                )
            context["simulation_compiled"] = True
    except Exception as err:
        context["exception"] = str(err)

    return render(request, "reviz/index.html", context)
