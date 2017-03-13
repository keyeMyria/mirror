/**
 * @author Teresa Uebber, Tobias Krauthoff
 * @email teresa.uebber@hhu.de, krauthoff@cs.uni-duesseldorf.de
 */

function DiscussionGraph(box_sizes_for_rescaling, is_partial_graph_mode) {
    var s;
    var isPartialGraphMode = is_partial_graph_mode;
    var isPositionVisible = false;
    var isContentVisible = false;
    var isStatementVisible = false;
    var isSupportVisible = false;
    var isAttackVisible = false;
    var isDefaultView = false;
    var light_grey = '#E0E0E0';
    var grey = '#848484';
    var yellow = '#FFC107';
    var red = '#F44336';
    var green = '#64DD17';
    var blue = '#3D5AFE';
    var black = '#000000';
    var dark_grey = '#424242';
    var dark_red = '#D32F2F';
    var dark_green = '#689F38';
    var dark_blue = '#1976D2';
    var font_size = 14; // needed for rescaling
    var line_height = 1.5; // needed for rescaling
    var box_sizes = box_sizes_for_rescaling; // needed for rescaling
    var node_id_prefix = 'node_'; // needed for rescaling
    var old_scale = 1.0; // needed for rescaling
    var zoom_scale;
    var statement_size = 6; // base node size of an statement
    var node_factor_size = 10; // additional size for the doj, which is in [0,1]
    var rel_node_factor;
    var currentColorOfCircle;
    var selectedCircleId;
    var node_size = 6;
    var issue_size = 8;
    var edge_size = 90;
    var edge_size_on_virtual_nodes = 45;

    /**
     * Displays a graph of current discussion
     */
    this.showGraph = function (override_cases) {
        var url = window.location.href.split('?')['0'];
        url = url.split('#')[0];
        var is_argument = null;
        var uid = null;
        var tmp = url.split('/');
        isPartialGraphMode = override_cases;
        if (!override_cases) {
	        if (url.indexOf('attitude') != -1) {
		        uid = tmp[tmp.indexOf('attitude') + 1];
		        is_argument = false;
		        isPartialGraphMode = true;
	        } else if (url.indexOf('justify') != -1) {
		        uid = tmp[tmp.indexOf('justify') + 1];
		        is_argument = false;
		        isPartialGraphMode = true;
	        } else if (url.indexOf('reaction') != -1) {
		        uid = tmp[tmp.indexOf('reaction') + 1];
		        is_argument = true;
		        isPartialGraphMode = true;
	        } else if (url.indexOf('support') != -1) {
		        uid = tmp[tmp.indexOf('support') + 1];
		        is_argument = true;
		        isPartialGraphMode = true;
	        }
        }
	    new AjaxGraphHandler().getDiscussionGraphData(this, uid, is_argument, isPartialGraphMode);
    };

    /**
     * Callback if ajax request was successful.
     *
     * @param data
     * @param request_for_complete
     */
    this.callbackIfDoneForDiscussionGraph = function (data, request_for_complete) {
        var jsonData = $.parseJSON(data);
        console.log(jsonData);
        if (jsonData.error.length != 0){
        	setGlobalErrorHandler('Ohh!', jsonData.error);
        	new GuiHandler().setDisplayStyleAsDiscussion();
        	return;
        }
        s = new DiscussionGraph(box_sizes, isPartialGraphMode).setDefaultViewParams(true, jsonData, null, request_for_complete);
    };

    /**
     * If ajax request was successful show modal with data for jump into discussion.
     *
     * @param data
     */
    this.callbackIfDoneForGetJumpDataForGraph = function (data) {
        var jsonData = $.parseJSON(data);
        var popup = $('#popup-jump-graph');
        if (jsonData.error.length === 0) {
            var list = $('<ul>');
            popup.find('div.modal-body div').empty();
            createContentOfModalBody(jsonData, list);
            popup.find('div.modal-body div').append(list);

            // jump to url
            popup.find('input').click(function () {
                window.location = $(this).attr('value');
            });
        } else {
            popup.modal('hide');
        }

        // add hover effects
        new GuiHandler().hoverInputListOf(popup.find('div.modal-body div'));
    };

    /**
     * Create content for modal to jump into discussion.
     *
     * @param jsonData
     * @param list
     */
    function createContentOfModalBody(jsonData, list) {
        var label, input, element, counter = 0;

        $.each(jsonData.arguments, function (key, value) {
            input = $('<input>').attr('type', 'radio').attr('value', value.url).attr('id', 'jump_' + counter);
            label = $('<label>').html(value.text).attr('for', 'jump_' + counter);
            element = $('<li>').append(input).append(label);
            list.append(element);
            counter += 1;
        });
    }

    /**
     * Set parameters for default view of graph.
     *
     * @param startD3
     * @param jsonData
     * @param d3
     * @param request_for_complete
     */
    this.setDefaultViewParams = function (startD3, jsonData, d3, request_for_complete) {
    	var dg = new DiscussionGraph(box_sizes, isPartialGraphMode);
	    $('#global-view').attr('data-global-view-loaded', jsonData['type'] == 'complete');
        dg.setButtonDefaultSettings(jsonData, request_for_complete);
        var container = $('#' + graphViewContainerSpaceId);
        container.empty();

        if (startD3) {
            if (!this.getD3Graph(jsonData))
                dg.setDefaultViewParams(false, null, d3, request_for_complete);
        } else {
            container.empty();
        }
    };

    /**
     * Set default settings of buttons.
     */
    this.setButtonDefaultSettings = function (jsonData, request_for_complete) {
    	$('#graph-view-container').find('.sidebar').find('li').each(function(){
    		$(this).removeClass('hidden');
	    });
    	
        $('#show-labels').show();
        $('#hide-labels').hide();
        $('#show-my-statements').show();
        $('#hide-my-statements').hide();
        $('#show-attacks-on-my-statements').show();
        $('#hide-attacks-on-my-statements').hide();
        $('#show-supports-on-my-statements').show();
        $('#hide-supports-on-my-statements').hide();
        $('#show-positions').show();
        $('#hide-positions').hide();
        if ((request_for_complete || typeof request_for_complete === 'undefined') && !isPartialGraphMode){
        	$('#global-view').hide();
        } else {
        	$('#global-view').show();
        }
        
        // show or hide my path
	    $('#hide-my-path').hide();
        if (jsonData.path.length == 0) {
            $('#show-my-path').addClass('hidden');
        } else {
            $('#show-my-path').show();
        }
    };

    /**
     * Create a graph.
     *
     * @param jsonData
     */
    this.getD3Graph = function (jsonData) {
        var container = $('#' + graphViewContainerSpaceId);
        container.empty();
        rel_node_factor = {};
        //rel_node_factor = 'node_doj_factors' in jsonData ? jsonData.node_doj_factors : {};
        //rel_node_factor = 'node_opinion_factors' in jsonData? jsonData.node_opinion_factors : {};

        // height of the header (offset per line count)
        var offset = ($('#' + graphViewContainerHeaderId).outerHeight() / 26 - 1 ) * 26;

        var width = container.width();
        var height = container.outerHeight() - offset;

        var svg = getGraphSvg(width, height);
        var force = getForce(width, height, jsonData);

        // zoom and pan
        var zoom = d3.behavior.zoom();
        zoomAndPan(zoom);
        var drag = enableDrag(force);

        // resize
        resizeGraph(container, force);

        // edge
        var edges = createEdgeDict(jsonData);
        setNodeColorsForData(jsonData);
        // create arrays of links, nodes and move layout forward one step
        force.links(edges).nodes(jsonData.nodes).on("tick", forceTick);
        var edgesTypeArrow = createArrowDict(edges);
        var marker = createArrows(svg, edgesTypeArrow);
        var link = createLinks(svg, edges, marker);

        // node
        var node = createNodes(svg, force, drag);
        var circle = setNodeProperties(node).attr('class', 'circle');

        // tooltip
        // rect as background of label
        var tooltip = node.append('g');
        var rect = tooltip.append('rect').attr('class', 'labelBox');
        var label = createLabel(tooltip);

        // reorder the elements so that the tooltips appear in front of the nodes
        tooltip.order();

        setRectProperties(rect);

        // legend
        createLegend();
        // call updated legend
        var legend = d3.svg.legend();
        // create div for legend
        container.append("<div id = 'graphViewLegendId'></div>");
        getLegendSvg().call(legend);

        // buttons of sidebar
        addListenersForSidebarButtons(jsonData, label, rect, edges, force, zoom);
        // add listener to show/hide tooltip on mouse over
        addListenerForTooltip();

        // update force layout calculations
        function forceTick() {
            // update position of edges
            link.attr({
                x1: function (d) {
                    return d.source.x;
                },
                y1: function (d) {
                    return d.source.y;
                },
                x2: function (d) {
                    return getPositionOfLink("x2", d.target.x, edges, d);
                },
                y2: function (d) {
                    return getPositionOfLink("y2", d.target.y, edges, d);
                }
            });

            // update position of rect
            rect.attr("transform", function (d) {
                return "translate(" + d.x + "," + (d.y - 50) + ")";
            });

            // update position of nodes
            circle.attr({
                cx: function (d) {
                    return d.x;
                },
                cy: function (d) {
                    return d.y;
                }
            });

            // update position of label
            label.attr("transform", function (d) {
                return "translate(" + d.x + "," + (d.y - 50) + ")";
            });
        }

        force.start();


        //////////////////////////////////////////////////////////////////////////////
        // highlight nodes and edges
        addListenerForNodes(circle, edges);

        return true;
    };

    /**
     * Calculate coordinate of link for undercuts.
     *
     * @param linkTargetCoordinate
     * @param nodeCoordinate
     * @param edges
     * @param d
     * @returns {*}
     */
    function getPositionOfLink(linkTargetCoordinate, nodeCoordinate, edges, d) {
        var position;
        var edge;
        if (d.is_undercut === true && d.target_edge != 'none') {
            edges.forEach(function (e) {
                if (e.id === d.target_edge) {
                    edge = e;
                }
            });
            try {
	            if (linkTargetCoordinate === 'x2') {
		            position = (parseInt(d3.select('#link-' + edge.id).attr('x2')) + parseInt(d3.select('#link-' + edge.id).attr('x1'))) / 2;
	            } else {
		            position = (parseInt(d3.select('#link-' + edge.id).attr('y2')) + parseInt(d3.select('#link-' + edge.id).attr('y1'))) / 2;
	            }
            } catch (TypeError){
            	console.log('TypeError in getPositionOfLink while selecting link');
            }
        } else {
            position = nodeCoordinate;
        }
        return position;
    }

    /**
     * Create svg-element.
     *
     * @param width: width of container, which contains graph
     * @param height: height of container
     * @return scalable vector graphic
     */
    function getGraphSvg(width, height) {
        return d3.select('#' + graphViewContainerSpaceId).append("svg")
            .attr({width: width, height: height, id: "graph-svg"})
            .append('g')
            .attr("class", "zoom");
    }

    /**
     * Create force-directed network diagram and define properties.
     *
     * @param width: width of container, which contains graph
     * @param height: height of container
     * @param jsonData
     * @return force layout
     */
    function getForce(width, height, jsonData) {
        //var factor = jsonData.nodes.length/5 * 100;
        var factor = 800;
        return d3.layout.force()
            .size([width, height])
            // nodes push each other away
            .charge(-factor)
            .linkDistance(function (d) {
                  return d.size;
            });
    }

    /**
     * Enable zoom and pan functionality on graph.
     */
    function zoomAndPan(zoom) {
        zoom.on("zoom", redraw).scaleExtent([0.5, 5]);

        d3.select("#graph-svg").call(zoom).on("dblclick.zoom", null);

        // if default view button is clicked redraw graph once
        if(isDefaultView){
            redraw();
        }

        function redraw() {
            var change_scale = true;
            if(isDefaultView){
                zoom_scale = 1;
                isDefaultView = false;
            }
            else{
                zoom_scale = zoom.scale();
                change_scale = Math.abs(old_scale - zoom_scale) > 0.02;
            }

            old_scale = zoom_scale;

            d3.selectAll("g.zoom").attr("transform", "translate(" + zoom.translate() + ")" + " scale(" + zoom_scale + ")");

            if (change_scale) {
                // resizing of font size, line height and the complete rectangle
                $('#graph-svg').find('.node').each(function () {
                    var id = $(this).attr('id').replace(node_id_prefix, '');
                    if (id.indexOf('statement') != -1 || id.indexOf('issue') != -1) {
                        $('#label-' + id).css({
                            'font-size': font_size / zoom_scale + 'px',
                            'line-height': line_height / zoom_scale
                        });
                        var width = box_sizes[id].width / zoom_scale;
                        var height = box_sizes[id].height / zoom_scale;
                        var pos = calculateRectPos(box_sizes[id].width, box_sizes[id].height);
                        $('#rect-' + id).attr({
                            'width': width,
                            'height': height,
                            'x': pos[0] / zoom_scale,
                            'y': pos[1] / zoom_scale
                        });
                    }
                });

                // dirty hack to accept new line height and label position
                $('#graph-svg').css({'line-height': '1.0'});
                setTimeout(function () {
                    $('#graph-svg').css({'line-height': '1.5'});
                    $('#' + graphViewContainerSpaceId).find('.node').each(function () {
                        var id = $(this).attr('id').replace(node_id_prefix, '');
                        var label = $('#label-' + id);
                        var rect = $('#rect-' + id);
                        label.attr({
                            'y': -label.height() / zoom_scale + 45 / zoom_scale
                        });
                    });
                }, 300);
            }
        }
    }

    /**
     * Enable drag functionality, because pan functionality overrides drag.
     *
     * @param force
     * @return drag functionality
     */
    function enableDrag(force) {
        return force.drag()
            .on("dragstart", function () {
                d3.event.sourceEvent.stopPropagation();
            });
    }

    /**
     * Resize graph on window event.
     *
     * @param container
     * @param force
     */
    function resizeGraph(container, force) {
        d3.select(window).on("resize", resize);
        function resize() {
            var graphSvg = $('#graph-svg');
            graphSvg.width(container.width());
            // height of space between header and bottom of container
            graphSvg.height(container.outerHeight() - $('#graph-view-container-header').height() + 20);
            force.size([container.width(), container.outerHeight()]).resume();
        }
    }

    /**
     * Sets the color in the json Data
     *
     * @param jsonData: dict with data for nodes and edges
     */
    function setNodeColorsForData(jsonData) {
        jsonData.nodes.forEach(function (e) {
            if (e.type === 'position')       e.color = blue;
            else if (e.type === 'statement') e.color = yellow;
            else if (e.type === 'issue')     e.color = grey;
            else                             e.color = black;
        });
    }

    /**
     * Create dictionary for edges.
     *
     * @param jsonData: dict with data for nodes and edges
     * @return edges: array, which contains dicts for edges
     */
    function createEdgeDict(jsonData) {
        var edges = [];
        jsonData.edges.forEach(function (e) {
            // get source and target nodes
            var sourceNode = jsonData.nodes.filter(function (d) {
                    return d.id === e.source;
                })[0],
                targetNode = jsonData.nodes.filter(function (d) {
                    return d.id === e.target;
                })[0];
            // add edge, color, type, size and id to array
            var color = e.is_attacking === 'none' ? dark_grey : e.is_attacking ? red : green;
            edges.push({
                source: sourceNode,
                target: targetNode,
                color: color,
                edge_type: e.edge_type,
                size: edge_size,
                id: e.id,
                is_attacking: e.is_attacking,
                target_edge: e.target_edge,
                is_undercut: e.is_undercut
            });
        });
        return edges;
    }

    /**
     * Select edges with type of arrow.
     *
     * @param edges: edges of graph
     * @return Array array, which contains edges of type arrow
     */
    function createArrowDict(edges) {
        var edgesTypeArrow = [];
        edges.forEach(function (d) {
            if (d.edge_type === 'arrow') {
                return edgesTypeArrow.push(d);
            }
        });
        return edgesTypeArrow;
    }

    /**
     * Create arrows for edges.
     *
     * @param svg
     * @param edgesTypeArrow
     * @return marker: arrow
     */
    function createArrows(svg, edgesTypeArrow) {
        return svg.append("defs").selectAll('marker').data(edgesTypeArrow)
            .enter().append("svg:marker")
            .attr({
                id: function (d) {
                    return "marker_" + d.edge_type + d.id;
                },
                refX: function (d) {
                    if(d.is_undercut === true){
                        return 6;
                    }
                    return 6 + calculateNodeSize(d.target) / 2;
                },
                refY: 0,
                markerWidth: 10, markerHeight: 10,
                viewBox: '0 -5 10 10',
                orient: "auto",
                fill: function (d) {
                    return d.color;
                }
            })
            .append("svg:path")
            .attr("d", "M0,-3L7,0L0,3");
    }

    /**
     * Create links between nodes.
     *
     * @param svg
     * @param marker: arrow
     * @param edges
     * @return links
     */
    function createLinks(svg, edges, marker) {
        return svg.selectAll(".path")
            .data(edges)
            // svg lines
            .enter().append("line")
            .attr({
                'class': "link",
                'id': function (d) { return 'link-' + d.id; }
            })
            .style("stroke", function (d) {
                return d.color;
            })
            // assign marker to line
            .attr("marker-end", function (d) {
                return "url(#marker_" + d.edge_type + d.id + ")";
            });
    }

    /**
     * Create node as svg circle and enable drag functionality.
     *
     * @param svg
     * @param force
     * @param drag
     * @return nodes
     */
    function createNodes(svg, force, drag) {
        return svg.selectAll(".node")
            .data(force.nodes())
            .enter().append("g")
            .attr({
                'class': "node",
                'id': function (d) { return node_id_prefix + d.id; }
            })
            .call(drag);
    }

    /**
     * Define properties for nodes.
     *
     * @param node
     * @return circle
     */
    function setNodeProperties(node) {
        return node.append("circle")
            .attr({
                'r': function (d) { return calculateNodeSize(d); },
                'fill': function (d) { return d.color; },
                'id': function (d) { return 'circle-' + d.id; }
            });
    }

    /**
     * Calculates the node size in respect to the DOJ
     *
     * @param node
     * @returns {*}
     */
    function calculateNodeSize(node) {
        if (node.id.indexOf('statement_') != -1) {
            var id = node.id.replace('statement_', '');
            if (id in rel_node_factor)
                return node_size + node_factor_size * rel_node_factor[id];
            else
                return node_size;
        }
        if (node.id.indexOf('argument_') != -1)
            return 0;
        return issue_size;
    }

    /**
     * Wrap text.
     *
     * @param node
     * @return label
     */
    function createLabel(node) {
        return node.append("text").each(function (d) {
        	var text = $("<div>").html(d.label).text();
            var node_text = text.split(" ");
            for (var i = 0; i < node_text.length; i++) {
                if ((i % 4) == 0) {
                    d3.select(this).append("tspan")
                        .text(node_text[i])
                        .attr({
                            'dy': i ? '1.2em' : '0',
                            'x': '0',
                            'text-anchor': "middle"
                        });
                }
                else {
                    d3.select(this).append("tspan").text(' ' + node_text[i]);
                }
            }
            d3.select(this).attr("id", 'label-' + d.id);
            // set position of label
            var height = $("#label-" + d.id).height();
            d3.select(this).attr("y", -height + 45);
        });
    }

    /**
     * Set properties for rect.
     *
     * @param rect: background of label
     */
    function setRectProperties(rect) {
        rect.each(function (d) {
            var element = $("#label-" + d.id);
            var width = element.width() + 24;
            var height = element.height() + 10;
            var pos = calculateRectPos(width, height);
            // if d is a virtual node do not show label
            if (d.label === '') {
                width = 0;
                height = 0;
            }
            d3.select(this).attr({
                'width': width,
                'height': height,
                'x': pos[0],
                'y': pos[1],
                'id': 'rect-' + d.id
            });
            if (d.id.indexOf('statement') != -1 || d.id.indexOf('issue') != -1) {
                box_sizes[d.id] = {'width': width, 'height': height};
            }
        });
    }

    /**
     * Calculate the rectangle position depending on the rectangle width and height
     *
     * @param width int
     * @param height int
     * @returns {*[]} [x, y]
     */
    function calculateRectPos(width, height) {
        return [-width / 2, -height + 36];
    }

    /**
     * Create svg for legend.
     */
    function getLegendSvg() {
        d3.select('#graphViewLegendId').append("svg")
            .attr({
                'width': 200,
                'height': 200,
                'id': "graph-legend-svg"
            });
        return d3.select("#graph-legend-svg").append("g")
            .attr({
                'id': "graphLegend",
                'transform': "translate(10,20)"
            });
    }

    /**
     * Listen whether a node is clicked.
     *
     * @param circle
     * @param edges
     */
    function addListenerForNodes(circle, edges) {
        circle.on("click", function (d) {
            // distinguish between click and drag event
            if (d3.event.defaultPrevented) return;
            var circleId = this.id;
            showPartOfGraph(edges, circleId);
            selectedCircleId = d.id;
        });
        circle.on("dblclick", function (d) {
            // distinguish between click and drag event
            if (d3.event.defaultPrevented) return;
            // show modal when node clicked twice
            showModal(d);
            var circleId = this.id;
            showPartOfGraph(edges, circleId);
            selectedCircleId = d.id;
        });
    }

    /**
     * Create legend and update legend.
     */
    function createLegend() {
        // labels and colors for legend
        var legendLabelCircle = [_t_discussion("issue"), _t_discussion("position"), _t_discussion("statement")],
            legendLabelRect = [_t_discussion("support"), _t_discussion("attack")],
            legendColorCircle = [grey, blue, yellow],
            legendColorRect = [green, red];

        // set properties for legend
        return d3.svg.legend = function () {
            function legend(selection) {
                createNodeSymbols(selection, legendLabelCircle, legendColorCircle);
                createEdgeSymbols(selection, legendLabelRect, legendColorRect);
                createLabelsForSymbols(selection, legendLabelCircle, legendLabelRect);
                return this;
            }

            return legend;
        };
    }

    /**
     * Create symbols for nodes.
     *
     * @param selection
     * @param legendLabelCircle: array with labels for circle
     * @param legendColorCircle: array with colors
     */
    function createNodeSymbols(selection, legendLabelCircle, legendColorCircle) {
        selection.selectAll(".circle")
            .data(legendLabelCircle)
            .enter().append("circle")
            .attr({
                fill: function (d, i) {
                    return legendColorCircle[i];
                },
                r: statement_size,
                cy: function (d, i) {
                    return i * 40;
                }
            });
    }

    /**
     * Create symbols for edges.
     *
     * @param selection
     * @param legendLabelRect: array with labels for rect
     * @param legendColorRect: array with colors
     */
    function createEdgeSymbols(selection, legendLabelRect, legendColorRect) {
        selection.selectAll(".rect")
            .data(legendLabelRect)
            .enter().append("rect")
            .attr({
                fill: function (d, i) {
                    return legendColorRect[i];
                },
                'width': 15,
                'height': 5,
                'x': -7, y: function (d, i) { return i * 40 + 118; }
            });
    }

    /**
     * Create labels for symbols.
     *
     * @param selection
     * @param legendLabelCircle: array with labels for circle
     * @param legendLabelRect: array with labels for rect
     */
    function createLabelsForSymbols(selection, legendLabelCircle, legendLabelRect) {
        selection.selectAll(".text")
            .data(legendLabelCircle.concat(legendLabelRect))
            .enter().append("text")
            .text(function (d) {
                return d;
            })
            .attr({
                x: 20, y: function (d, i) {
                    return i * 40 + 5;
                }
            });
    }

    /**
     * Add listeners for buttons of sidebar.
     *
     * @param jsonData
     * @param label
     * @param rect
     * @param edges
     * @param force
     * @param zoom
     */
    function addListenersForSidebarButtons(jsonData, label, rect, edges, force, zoom) {
        $('#default-view').off('click').click(function () {
        	if ($('#global-view').attr('data-global-view-loaded') == 'true' && $('#global-view:hidden').length == 0)
	            new DiscussionGraph(box_sizes, isPartialGraphMode).showGraph(false);
	        else
	            showDefaultView(jsonData, force, edges, label, rect, zoom);
        });
        $('#global-view').off('click').click(function () {
        	if ($(this).attr('data-global-view-loaded') == 'true')
        		showDefaultView(jsonData, force, edges, label, rect, zoom);
	        else
                new DiscussionGraph(box_sizes, isPartialGraphMode).showGraph(true);
        });
        $('#show-labels').off('click').click(function () {
            showLabels(label, rect);
        });
        $('#hide-labels').off('click').click(function () {
            hideLabels(label, rect);
        });
        $('#show-positions').off('click').click(function () {
            showPositions();
        });
        $('#hide-positions').off('click').click(function () {
            hidePositions();
        });
        $('#show-my-path').off('click').click(function () {
            showPath(jsonData, edges);
        });
        $('#hide-my-path').off('click').click(function () {
            hidePath(edges);
        });
        $('#show-my-statements').off('click').click(function () {
            showMyStatements(edges, force);
        });
        $('#hide-my-statements').off('click').click(function () {
            hideMyStatements(edges, force);
        });
        $('#show-supports-on-my-statements').off('click').click(function () {
            showSupportsOnMyStatements(edges, force);
        });
        $('#hide-supports-on-my-statements').off('click').click(function () {
            hideSupportsOnMyStatements(edges, force);
        });
        $('#show-attacks-on-my-statements').off('click').click(function () {
            showAttacksOnMyStatements(edges, force);
        });
        $('#hide-attacks-on-my-statements').off('click').click(function () {
            hideAttacksOnMyStatements(edges, force);
        });
    }
	
	/**
     * Restore initial state of graph.
	 *
	 * @param jsonData
	 * @param force
	 * @param edges
	 * @param label
	 * @param rect
	 * @param zoom
	 */
    function showDefaultView(jsonData, force, edges, label, rect, zoom) {
        isDefaultView = true;

        // reset buttons
        new DiscussionGraph(box_sizes, isPartialGraphMode).setButtonDefaultSettings(jsonData);

        // set position of graph and set scale
        d3.selectAll("g.zoom").attr("transform", "translate(" + 0 + ")" + " scale(" + 1 + ")");

        // stop zoom event
        zoom.on("zoom", null);

        // create new zoom event listener
        var zoomDefaultView = d3.behavior.zoom();
        zoomAndPan(zoomDefaultView);

        resetButtons(label, rect, edges, force);
    }

    /**
     * Reset graph if button default view is clicked.
     *
     * @param label
     * @param rect
     * @param edges
     * @param force
     */
    function resetButtons(label, rect, edges, force) {
        isPositionVisible = true;
        isContentVisible = true;
        isStatementVisible = true;
        isSupportVisible = true;
        isAttackVisible = true;

        hideLabels(label, rect);
        hidePositions();
        hidePath(edges);
        hideMyStatements(edges, force);
        hideSupportsOnMyStatements(edges, force);
        hideAttacksOnMyStatements(edges, force);
    }

    /**
     * Show all labels of graph.
     *
     * @param label
     * @param rect
     */
    function showLabels(label, rect) {
        isContentVisible = true;
        isPositionVisible = true;

        label.style("display", 'inline');
        rect.style("display", 'inline');

        hideLabelsOfNotSelectedNodes();

        $('#show-labels').hide();
        $('#hide-labels').show();
        // also show content of positions
        $('#show-positions').hide();
        $('#hide-positions').show();
    }

    /**
     * Hide labels of not selected nodes
     */
    function hideLabelsOfNotSelectedNodes() {
        // hide labels of nodes which are not selected
        d3.selectAll(".node").each(function (d) {
            if (d3.select('#circle-' + d.id).attr('fill') == light_grey) {
                d3.select('#label-' + d.id).style("display", 'none');
                d3.select("#rect-" + d.id).style("display", 'none');
            }
        });
    }

    /**
     * Hide all labels of graph.
     *
     * @param label
     * @param rect
     */
    function hideLabels(label, rect) {
        isContentVisible = false;
        label.style("display", 'none');
        rect.style("display", 'none');
        $('#show-labels').show();
        $('#hide-labels').hide();
        addListenerForTooltip();
        if (isPositionVisible) {
            $('#show-positions').show();
            $('#hide-positions').hide();
        }
        isPositionVisible = false;
    }

    /**
     * Show labels for positions.
     */
    function showPositions() {
        isPositionVisible = true;
        // select positions
        setDisplayStyleOfNodes('inline');
        $('#show-positions').hide();
        $('#hide-positions').show();
    }

    /**
     * Hide labels for positions.
     */
    function hidePositions() {
        isPositionVisible = false;
        addListenerForTooltip();
        // select positions
        setDisplayStyleOfNodes('none');
        $('#show-positions').show();
        $('#hide-positions').hide();
    }

    /**
     * Show current path.
     *
     * @param jsonData
     * @param edges
     */
    function showPath(jsonData, edges) {
        $('#show-my-path').hide();
        $('#hide-my-path').show();

        edges.forEach(function (d) {
            grayingElements(d);
        });

        if(jsonData.path.length != 0) { // if jsonData.path is not empty highlight path
            highlightPath(jsonData, edges);
        } else{ // if jsonData.path is empty color issue
            d3.select('#circle-issue').attr('fill', grey);
        }
    }

    /**
     * Highlight path.
     *
     * @param jsonData
     * @param edges
     */
    function highlightPath(jsonData, edges) {
        let edgesCircleId = [];

        // run through all values in jsonData.path
        jsonData.path.forEach(function (d) {
            edges.forEach(function (edge) {
                // edge without virtual node
                if((edge.source.id === getId(d[0])) && (edge.target.id === getId(d[1]))) {
                    edgesCircleId.push(edge);
                }
                // edge with virtual node
                else if(edge.source.id == getId(d[0]) && edge.target.label == ''){
                    findEdgesVirtualNode(edges, edge, edgesCircleId, d);
                }
            });
        });

        // highlight path
        edgesCircleId.forEach(function (d) {
            highlightElements(d);
        });
    }

    /**
     * Find two edges which connect source and target.
     *
     * @param edges
     * @param edge
     * @param edgesCircleId
     */
    function findEdgesVirtualNode(edges, edge, edgesCircleId, d){
        // edge from virtual node to statement
        edges.forEach(function (e) {
            if (e.source.id == edge.target.id && e.target.id == getId(d[1])) {
                edgesCircleId.push(edge);
                edgesCircleId.push(e);
            }
        });
    }

    /**
     * Get id of node.
     *
     * @param node
     * @returns {*}
     */
    function getId(node) {
        if(node == "issue"){
            return node;
        }
        return "statement_" + node;
    }

    /**
     * Hide current path.
     *
     * @param edges
     */
    function hidePath(edges) {
        $('#show-my-path').show();
        $('#hide-my-path').hide();
        edges.forEach(function (d) {
            highlightElements(d);
        });
    }

    /**
     * Show all statements, which the current user has created.
     *
     * @param edges
     * @param force
     */
    function showMyStatements(edges, force) {
        isStatementVisible = true;

        // hide supports and attacks on statements
        if (isSupportVisible) {
            $('#show-supports-on-my-statements').show();
            $('#hide-supports-on-my-statements').hide();
            isSupportVisible = false;
        }
        if (isAttackVisible) {
            $('#show-attacks-on-my-statements').show();
            $('#hide-attacks-on-my-statements').hide();
            isAttackVisible = false;
        }

        // graying all elements of graph
        edges.forEach(function (d) {
            grayingElements(d);
        });

        selectSupportsAttacks(edges, force);

        $('#show-my-statements').hide();
        $('#hide-my-statements').show();
    }

    /**
     * Hide all statements, which the current user has created.
     *
     * @param edges
     * @param force
     */
    function hideMyStatements(edges, force) {
        isStatementVisible = false;

        // hide supports and attacks on statements
        if (isSupportVisible) {
            $('#show-supports-on-my-statements').show();
            $('#hide-supports-on-my-statements').hide();
            isSupportVisible = false;
        }
        if (isAttackVisible) {
            $('#show-attacks-on-my-statements').show();
            $('#hide-attacks-on-my-statements').hide();
            isAttackVisible = false;
        }

        highlightAllElements(edges);

        // delete border of nodes
        deleteBorderOfCircle(force);

        $('#show-my-statements').show();
        $('#hide-my-statements').hide();
    }

    /**
     * Show all supports on the statements, which the current user has created.
     *
     * @param edges
     * @param force
     */
    function showSupportsOnMyStatements(edges, force) {
        isSupportVisible = true;

        // hide statements
        // delete border of nodes
        deleteBorderOfCircle(force);
        $('#show-my-statements').show();
        $('#hide-my-statements').hide();
        isStatementVisible = false;

        // if attacks on statements of current user are visible, highlight additionally the supports
        if (!isAttackVisible) {
            // graying all elements of graph
            edges.forEach(function (d) {
                grayingElements(d);
            });
        }

        selectSupportsAttacks(edges, force);

        $('#show-supports-on-my-statements').hide();
        $('#hide-supports-on-my-statements').show();
    }

    /**
     * Hide all supports on the statements, which the current user has created.
     *
     * @param edges
     * @param force
     */
    function hideSupportsOnMyStatements(edges, force) {
        isSupportVisible = false;

        deleteBorderOfCircle(force);

        // if attacks are not visible, show the default view of the graph
        // else make them visible
        if (!isAttackVisible) {
            highlightAllElements(edges);
        }
        else {
            showAttacksOnMyStatements(edges, force);
        }

        $('#show-supports-on-my-statements').show();
        $('#hide-supports-on-my-statements').hide();
    }

    /**
     * Show all attacks on the statements, which the current user has created.
     *
     * @param edges
     * @param force
     */
    function showAttacksOnMyStatements(edges, force) {
        isAttackVisible = true;

        // hide statements
        // delete border of nodes
        deleteBorderOfCircle(force);
        $('#show-my-statements').show();
        $('#hide-my-statements').hide();
        isStatementVisible = false;

        // if supports on statements of current user are visible, highlight additionally the attacks
        if (!isSupportVisible) {
            // graying all elements of graph
            edges.forEach(function (d) {
                grayingElements(d);
            });
        }

        selectSupportsAttacks(edges, force);

        $('#show-attacks-on-my-statements').hide();
        $('#hide-attacks-on-my-statements').show();
    }

    /**
     * Hide all attacks on the statements, which the current user has created.
     *
     * @param edges
     * @param force
     */
    function hideAttacksOnMyStatements(edges, force) {
        isAttackVisible = false;

        deleteBorderOfCircle(force);

        if (!isSupportVisible) {
            highlightAllElements(edges);
        }
        else {
            showSupportsOnMyStatements(edges, force);
        }
        $('#show-attacks-on-my-statements').show();
        $('#hide-attacks-on-my-statements').hide();
    }

    /**
     * Highlight all elements of graph.
     *
     * @param edges
     */
    function highlightAllElements(edges) {
        edges.forEach(function (d) {
            highlightElements(d);
        });
    }

    /**
     * Select supports or attacks on statements of current user.
     *
     * @param edges
     * @param force
     */
    function selectSupportsAttacks(edges, force) {
        let circleIds = [];
        // highlight supports or attacks on statements, which the current user has created
        force.nodes().forEach(function (d) {
            if (d.author.name === $('#header_nickname')[0].innerText) {
                circleIds.push(d.id);
            }
        });
        // show attacks or supports on statements of current user
        // if button "show statements" is not selected
        if(!isStatementVisible){
            showAttacksSupports(edges, circleIds);
        }
        else{
            // highlight all statements of current user
            force.nodes().forEach(function (d) {
                if($.inArray(d.id, circleIds) != -1) {
                    d3.select('#circle-' + d.id).attr({fill: d.color, stroke: 'black'});
                }
            });
        }
    }

    /**
     * Delete border of circle.
     *
     * @param force
     */
    function deleteBorderOfCircle(force){
        // delete border of nodes
        force.nodes().forEach(function (d) {
            d3.select('#circle-' + d.id).attr('stroke', 'none');
        });
    }

    /**
     * Set display style of nodes.
     *
     * @param style
     */
    function setDisplayStyleOfNodes(style) {
        // select edges with position as source and issue as target
        d3.selectAll(".node").each(function (d) {
            d3.selectAll(".link").each(function (e) {
                // only show labels of highlighted nodes
                if (e.source.id === d.id && e.target.id === 'issue' && d3.select('#circle-' + d.id).attr('fill') != light_grey) {
                    // set display style of positions
                    d3.select('#label-' + d.id).style("display", style);
                    d3.select("#rect-" + d.id).style("display", style);
                }
            });
        });
    }

    /**
     * Show/hide tooltips on mouse event.
     */
    function addListenerForTooltip() {
        d3.selectAll('.node').on("mouseover", function (d) {
            determineShowOrHideTooltip(d, true);
        }).on("mouseout", function (d) {
            determineShowOrHideTooltip(d, false);
        });
    }

    /**
     * Show or hide tooltip of node dependent on selected side-bar buttons.
     *
     * @param d: current node
     * @param mouseover
     */
    function determineShowOrHideTooltip(d, mouseover) {
        var isPosition = testNodePosition(d);
        if(isPositionVisible && isContentVisible){
        }
        else if(!isPositionVisible && !isContentVisible){
            showHideTooltip(d, mouseover);
        }
        else if(!isPosition && isPositionVisible){
            showHideTooltip(d, mouseover);
        }
        else if(isPosition && isContentVisible){
            showHideTooltip(d, mouseover);
        }
    }

    /**
     * Test whether the selected node is a position.
     *
     * @param d
     */
    function testNodePosition(d){
        var isPosition = false;
        d3.selectAll(".link").each(function (e) {
            if (e.source.id === d.id && e.target.id === 'issue') {
                isPosition = true;
            }
        });
        return isPosition;
    }

    /**
     * Show or hide tooltip of node dependent on mouse event.
     *
     * @param d
     * @param mouseover
     */
    function showHideTooltip(d, mouseover) {
        // if there is a mouseover-event show the tooltip
        if(mouseover){
            d3.select('#label-' + d.id).style('display', 'inline');
            d3.select('#rect-' + d.id).style('display', 'inline');
            // determine color of circle before mouse over
            // to restore color on mouse out
            currentColorOfCircle = d3.select('#circle-' + d.id).attr('fill');
            d3.select('#circle-' + d.id).attr('fill', '#757575');
        }
        // otherwise there is a mouseout-out, then hide the tooltip
        else{
            d3.select('#label-' + d.id).style('display', 'none');
            d3.select('#rect-' + d.id).style('display', 'none');
            // if circle d is currently clicked restore originally color of circle
            if(d.id === selectedCircleId){
                d3.select('#circle-' + d.id).attr('fill', d.color);
            }
            else{
                d3.select('#circle-' + d.id).attr('fill', currentColorOfCircle);
            }
        }
    }

    /**
     * Show modal.
     */
    function showModal(d) {
        var popup = $('#popup-jump-graph');
        if (d.id != 'issue') {
            popup.modal('show');
            var splitted = d.id.split('_'),
                uid = splitted[splitted.length - 1];
            new AjaxGraphHandler().getJumpDataForGraph(uid);
        }
    }

    /**
     * Select uid.
     */
    function selectUid(id) {
        var splitted = id.split('-');
        return splitted[splitted.length - 1];
    }

    /**
     * Highlight incoming and outgoing edges of selected nodes.
     *
     * @param edges: all edges of graph
     * @param circleIds: id of selected node
     */
    function showAttacksSupports(edges, circleIds) {
        // edges with selected statement as target
        let edgesCircleId = [];

        // edge with circleUid as target
        circleIds.forEach(function (circleId) {
            edges.forEach(function (e) {
                if (e.target.id === circleId) {
                    // if supports and attacks is clicked
                    if (isSupportVisible && isAttackVisible) {
                        edgesCircleId.push(e);
                        findVirtualNodes(edges, edgesCircleId, e);
                    }
                    // if attacks is clicked
                    else if (isAttackVisible && (e.color === red)) {
                        if (!(e.is_undercut == true)) {
                            edgesCircleId.push(e);
                            findUndercutsForEdge(edges, edgesCircleId, e);
                            findVirtualNodes(edges, edgesCircleId, e);
                        }
                    }
                    // if supports is clicked
                    else if (isSupportVisible && (e.color === green)) {
                        edgesCircleId.push(e);
                        findVirtualNodes(edges, edgesCircleId, e);
                    }
                }
            });
        });

        // highlight incoming edges
        edgesCircleId.forEach(function (d) {
            // add border to statements of user, if they are source or target of edge in edgesCircleId
            if(($.inArray(d.source.id, circleIds) != -1) && (d.is_undercut == 'none')){
                d3.select('#circle-' + d.source.id).attr({'fill': d.source.color, 'stroke': 'black'});
            }
            if(($.inArray(d.target.id, circleIds) != -1) && (d.is_undercut == 'none')){
                d3.select('#circle-' + d.target.id).attr({'fill': d.target.color, 'stroke': 'black'});
            }
            highlightElements(d);
        });
    }

    /**
     * Highlight incoming and outgoing edges of selected node.
     *
     * @param edges: all edges of graph
     * @param circleId: id of selected node
     */
    function showPartOfGraph(edges, circleId) {
        // edges with selected circle as source or as target
        var edgesCircleId = [];
        var circleUid = selectUid(circleId);

        // edge with circleUid as source
        var edgesWithSourceCircleUid = [];
        edges.forEach(function (e) {
            if(e.source.id === circleUid){
                edgesWithSourceCircleUid.push(e);
            }
        });

        if(circleUid == 'issue'){
            // circleUid is equal to 'issue'
            edges.forEach(function (e) {
                if (e.target.id === circleUid) {
                    edgesCircleId.push(e);
                }
            });
        }
        else {
            // edge is an undercut
            edgesWithSourceCircleUid.forEach(function (edge) {
                testEdgeUndercut(edges, edgesCircleId, edge);
            });

            // undercuts on edge of circleUid to target or of source to circleUid
            findUndercuts(edges, edgesCircleId, circleUid);
        }

        // if isMyStatementsClicked is false gray all elements at each function call,
        // else the graph is colored once gray
        if (!isStatementVisible && !isSupportVisible && !isAttackVisible) {
            edges.forEach(function (d) {
                grayingElements(d);
            });
        }
        edgesCircleId.forEach(function (d) {
            highlightElements(d);
        });
    }

    /**
     * Test if edge is an undercut.
     *
     * @param edges
     * @param edgesCircleId
     * @param edge
     */
    function testEdgeUndercut(edges, edgesCircleId, edge) {
        if (edge.is_undercut == true) {
            // highlight undercut on edge
            edges.forEach(function (e) {
                if (e.target_edge === edge.id) {
                    edgesCircleId.push(e);
                    findVirtualNodes(edges, edgesCircleId, e);
                }
            });
            // target edge of undercut
            var targetEdge = getTargetEdgeOfEdge(edges, edgesCircleId, edge);

            // edge is an undercut on an undercut
            if (targetEdge.is_undercut === true) {
                // find target edge of target edge of edge
                getTargetEdgeOfEdge(edges, edgesCircleId, targetEdge);
            }
        }
    }

    /**
     * Find all undercuts on edges.
     *
     * @param edges
     * @param edgesCircleId
     * @param circleUid
     */
    function findUndercuts(edges, edgesCircleId, circleUid){
        // incoming or outgoing edges of node
        var sourceTargetEdges = [];
        // undercuts
        // highlight all incoming and outgoing edges
        edges.forEach(function (e) {
            if((e.target.id == circleUid) || (e.source.id == circleUid)) {
                sourceTargetEdges.push(e);
                // test if source or target of e is a virtual node
                findVirtualNodes(edges, edgesCircleId, e);
                edgesCircleId.push(e);
            }
        });
        sourceTargetEdges.forEach(function (k) {
            findUndercutsForEdge(edges, edgesCircleId, k);
        });
    }

    /**
     * Highlight all undercuts on given edge.
     *
     * @param edges
     * @param edgesCircleId
     * @param edge
     */
    function findUndercutsForEdge(edges, edgesCircleId, edge){
        var undercuts = [];
        // undercuts on edge
        edges.forEach(function (e) {
            if ((e.is_undercut == true) && (e.target_edge === edge.id)) {
                undercuts.push(e);
                edgesCircleId.push(e);
                findVirtualNodes(edges, edgesCircleId, e);
            }
        });
        // undercuts on undercuts on edge
        undercuts.forEach(function (k) {
            edges.forEach(function (e) {
                if ((e.is_undercut == true) && (e.target_edge === k.id)) {
                    edgesCircleId.push(e);
                    findVirtualNodes(edges, edgesCircleId, e);
                }
            });
        });
    }


    /**
     * Test if target or source of edge is a virtual node.
     *
     * @param edges
     * @param edgesCircleId
     * @param edge
     */
    function findVirtualNodes(edges, edgesCircleId, edge){
        if(edge.target.label === '' || edge.source.label === '') {
            edges.forEach(function (e) {
                // source of edge is virtual node or target of edge is virtual node
                if (((e.source.id === edge.target.id) || (e.target.id === edge.target.id)) && (edge.target.label === '')) {
                    if(!isSupportVisible){
                        findUndercutsForEdge(edges, edgesCircleId, e);
                        // check if e is an Undercut
                        testEdgeUndercut(edges, edgesCircleId, e);
                    }
                    edgesCircleId.push(e);
                }
                if (((e.source.id === edge.source.id) || (e.target.id === edge.source.id)) && (edge.source.label === '')) {
                    if(!isSupportVisible){
                        findUndercutsForEdge(edges, edgesCircleId, e);
                    }
                    edgesCircleId.push(e);
                }
            });
        }
    }

    /**
     * Find target edge of edge and add it to array edgesCircleId.
     *
     * @param edges
     * @param edgesCircleId
     * @param d
     */
    function getTargetEdgeOfEdge(edges, edgesCircleId, d){
        var targetEdge;
        edges.forEach(function (e) {
            // highlight all undercuts on undercut d
            if (e.target_edge === d.target_edge) {
                edgesCircleId.push(e);
            }
            if (e.id === d.target_edge) {
                targetEdge = e;
                findVirtualNodes(edges, edgesCircleId, targetEdge);
                edgesCircleId.push(e);
            }
        });
        return targetEdge;
    }

    /**
     * Highlighting components of graph.
     *
     * @param edge: edge that should be highlighted
     */
    function highlightElements(edge) {
        // edges
        d3.select('#link-' + edge.id).style('stroke', edge.color);
        // nodes
        d3.select('#circle-' + edge.source.id).attr('fill', edge.source.color);
        d3.select('#circle-' + edge.target.id).attr('fill', edge.target.color);
        // arrows
        d3.select("#marker_" + edge.edge_type + edge.id).attr('fill', edge.color);
    }

    /**
     * Graying components of graph.
     *
     * @param edge: edge that should be gray
     */
    function grayingElements(edge) {
        // edges
        d3.select('#link-' + edge.id).style('stroke', light_grey);
        // nodes
        d3.select('#circle-' + edge.source.id).attr('fill', light_grey);
        d3.select('#circle-' + edge.target.id).attr('fill', light_grey);
        // arrows
        d3.select("#marker_" + edge.edge_type + edge.id).attr('fill', light_grey);
    }
}