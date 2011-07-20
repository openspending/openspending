(function() {
/*
  This TreeUtil function is based on the JIT <http://thejit.orgt> authored by  Nicolas Garcia Belmonte, copyright 2008-2009 Nicolas Garcia Belmonte and licensed under the BSD License, see ...
 */

/*
   Object: TreeUtil

   Some common JSON tree manipulation methods.
*/
this.TreeUtil = {

	/*
	   Method: prune
	
	   Clears all tree nodes having depth greater than maxLevel.
	
	   Parameters:
	
		  tree - A JSON tree object. For more information please see <Loader.loadJSON>.
		  maxLevel - An integer specifying the maximum level allowed for this tree. All nodes having depth greater than max level will be deleted.

	*/
	prune: function(tree, maxLevel) {
		this.each(tree, function(elem, i) {
			if(i == maxLevel && elem.children) {
				delete elem.children;
				elem.children = [];
			}
		});
	},
	
	/*
	   Method: getParent
	
	   Returns the parent node of the node having _id_ as id.
	
	   Parameters:
	
		  tree - A JSON tree object. See also <Loader.loadJSON>.
		  id - The _id_ of the child node whose parent will be returned.

	  Returns:

		  A tree JSON node if any, or false otherwise.
	
	*/
	getParent: function(tree, id) {
		if(tree.id == id) return false;
		var ch = tree.children;
		if(ch && ch.length > 0) {
			for(var i=0; i<ch.length; i++) {
				if(ch[i].id == id) 
					return tree;
				else {
					var ans = this.getParent(ch[i], id);
					if(ans) return ans;
				}
			}
		}
		return false;	   
	},

	/*
	   Method: getSubtree
	
	   Returns the subtree that matches the given id.
	
	   Parameters:
	
		  tree - A JSON tree object. See also <Loader.loadJSON>.
		  id - A node *unique* identifier.
	
	   Returns:
	
		  A subtree having a root node matching the given id. Returns null if no subtree matching the id is found.

	*/
	getSubtree: function(tree, id) {
		if(tree.id == id) return tree;
		for(var i=0, ch=tree.children; i<ch.length; i++) {
			var t = this.getSubtree(ch[i], id);
			if(t != null) return t;
		}
		return null;
	},

	/*
	   Method: getLeaves
	
		Returns the leaves of the tree.
	
	   Parameters:
	
		  node - A JSON tree node. See also <Loader.loadJSON>.
		  maxLevel - _optional_ A subtree's max level.
	
	   Returns:
	
	   An array having objects with two properties. 
	   
		- The _node_ property contains the leaf node. 
		- The _level_ property specifies the depth of the node.

	*/
	getLeaves: function (node, maxLevel) {
		var leaves = [], levelsToShow = maxLevel || Number.MAX_VALUE;
		this.each(node, function(elem, i) {
			if(i < levelsToShow && 
			(!elem.children || elem.children.length == 0 )) {
				leaves.push({
					'node':elem,
					'level':levelsToShow - i
				});
			}
		});
		return leaves;
	},


	/*
	   Method: eachLevel
	
		Iterates on tree nodes with relative depth less or equal than a specified level.
	
	   Parameters:
	
		  tree - A JSON tree or subtree. See also <Loader.loadJSON>.
		  initLevel - An integer specifying the initial relative level. Usually zero.
		  toLevel - An integer specifying a top level. This method will iterate only through nodes with depth less than or equal this number.
		  action - A function that receives a node and an integer specifying the actual level of the node.
			
	  Example:
	 (start code js)
	   TreeUtil.eachLevel(tree, 0, 3, function(node, depth) {
		  alert(node.name + ' ' + depth);
	   });
	 (end code)
	*/
	eachLevel: function(tree, initLevel, toLevel, action) {
		if(initLevel <= toLevel) {
			action(tree, initLevel);
			for(var i=0, ch = tree.children; i<ch.length; i++) {
				this.eachLevel(ch[i], initLevel +1, toLevel, action);   
			}
		}
	},

	/*
	   Method: each
	
		A tree iterator.
	
	   Parameters:
	
		  tree - A JSON tree or subtree. See also <Loader.loadJSON>.
		  action - A function that receives a node.

	  Example:
	  (start code js)
		TreeUtil.each(tree, function(node) {
		  alert(node.name);
		});
	  (end code)
			
	*/
	each: function(tree, action) {
		this.eachLevel(tree, 0, Number.MAX_VALUE, action);
	},
	
	/*
	   Method: loadSubtrees
	
		Appends subtrees to leaves by requesting new subtrees
		with the _request_ method.
	
	   Parameters:
	
		  tree - A JSON tree node. <Loader.loadJSON>.
		  controller - An object that implements a request method.
	  
	   Example:
		(start code js)
		  TreeUtil.loadSubtrees(leafNode, {
			request: function(nodeId, level, onComplete) {
			  //Pseudo-code to make an ajax request for a new subtree
			  // that has as root id _nodeId_ and depth _level_ ...
			  Ajax.request({
				'url': 'http://subtreerequesturl/',
				
				onSuccess: function(json) {
				  onComplete.onComplete(nodeId, json);
				}
			  });
			}
		  });
		(end code)
	*/
	loadSubtrees: function(tree, controller) {
		var maxLevel = controller.request && controller.levelsToShow;
		var leaves = this.getLeaves(tree, maxLevel),
		len = leaves.length,
		selectedNode = {};
		if(len == 0) controller.onComplete();
		for(var i=0, counter=0; i<len; i++) {
			var leaf = leaves[i], id = leaf.node.id;
			selectedNode[id] = leaf.node;
			controller.request(id, leaf.level, {
				onComplete: function(nodeId, tree) {
					var ch = tree.children;
					selectedNode[nodeId].children = ch;
					if(++counter == len) {
						controller.onComplete();
					}
				}
			});
		}
	},

	/*
		Method: addNodeWithAncestors

		Add a node to the tree, creating all ancestor nodes as necessary.
	*/
	addNodeWithAncestors: function(tree, nodeIds, nodeDict) {
		if (nodeIds.length > 1) {
			parentNodeId = nodeIds[nodeIds.length-2];
		} else {
			parentNodeId = 'root';
		}
		var parentNode = this.getSubtree(tree, parentNodeId);
		if (parentNode==null) {
			parentNode = this.addNodeWithAncestors(tree, nodeIds.slice(0,-1), {});
		}
		// assume does not already exist
		var newNode = {
			'id': nodeIds[nodeIds.length-1],
			'children': []
		};
		for (var k in nodeDict) {
			newNode[k] = nodeDict[k];
		}
		parentNode.children.push(newNode);
		return newNode;
	},

	/*
	   Calculate the 'value' attribute for this node (and implicitly all descendants). Value for this node is sum of values of child nodes. If node is a leaf node and value not defined value is set to 0.

	   :return: node.value.
	*/
	calculateValues: function(node) {
		if (!node.value) {
			var total = 0;
			for(var i=0; i<node.children.length; i++) {
				total += this.calculateValues(node.children[i]);
			}
			node.value = total;
		}
		return node.value
	},
	
	/*
		Get the depth of node specified by nodeId within the tree.

		:return: an integer representing the level (root node has level 0).

		TODO: really inefficient (should reuse getParent code)
	*/
	getDepth: function(tree, nodeId) {
		if(tree.id == nodeId) return 0;
		var _parent = this.getParent(tree, nodeId);
		return 1 + this.getDepth(tree, _parent.id);
	}
};

})();
