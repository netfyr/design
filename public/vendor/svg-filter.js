/*!
* @svgdotjs/svg.filter.js - A plugin for svg.js adding filter functionality
* @version 3.0.10
* https://github.com/svgdotjs/svg.filter.js
*
* @copyright Wout Fierens
* @license MIT
*
* BUILT: 2026-09-15T07:16:45.901Z
*/;
import { Array as Array$1, Container, Defs, Element, extend, find, namespaces, nodeOrNew, utils, wrapWithAttrCheck } from "./svg.js";

//#region src/svg.filter.js
var Filter = class extends Element {
	constructor(node) {
		super(nodeOrNew("filter", node), node);
		this.$source = "SourceGraphic";
		this.$sourceAlpha = "SourceAlpha";
		this.$background = "BackgroundImage";
		this.$backgroundAlpha = "BackgroundAlpha";
		this.$fill = "FillPaint";
		this.$stroke = "StrokePaint";
		this.$autoSetIn = true;
	}
	put(element, i) {
		element = super.put(element, i);
		if (!element.attr("in") && this.$autoSetIn) element.attr("in", this.$source);
		if (!element.attr("result")) element.attr("result", element.id());
		return element;
	}
	remove() {
		this.targets().each("unfilter");
		return super.remove();
	}
	targets() {
		return find("svg [filter*=\"" + this.id() + "\"]");
	}
	toString() {
		return "url(#" + this.id() + ")";
	}
};
var Effect = class extends Element {
	constructor(node, attr) {
		super(node, attr);
		this.result(this.id());
	}
	in(effect) {
		if (effect == null) {
			const _in = this.attr("in");
			return this.parent() && this.parent().find(`[result="${_in}"]`)[0] || _in;
		}
		return this.attr("in", effect);
	}
	result(result) {
		return this.attr("result", result);
	}
	toString() {
		return this.result();
	}
};
var getAttrSetter = (params) => {
	return function(...args) {
		for (let i = params.length; i--;) if (args[i] != null) this.attr(params[i], args[i]);
	};
};
var updateFunctions = {
	blend: getAttrSetter([
		"in",
		"in2",
		"mode"
	]),
	colorMatrix: getAttrSetter(["type", "values"]),
	composite: getAttrSetter([
		"in",
		"in2",
		"operator"
	]),
	convolveMatrix: function(matrix) {
		matrix = new Array$1(matrix).toString();
		this.attr({
			order: Math.sqrt(matrix.split(" ").length),
			kernelMatrix: matrix
		});
	},
	diffuseLighting: getAttrSetter([
		"surfaceScale",
		"lightingColor",
		"diffuseConstant",
		"kernelUnitLength"
	]),
	displacementMap: getAttrSetter([
		"in",
		"in2",
		"scale",
		"xChannelSelector",
		"yChannelSelector"
	]),
	dropShadow: getAttrSetter([
		"in",
		"dx",
		"dy",
		"stdDeviation"
	]),
	flood: getAttrSetter(["flood-color", "flood-opacity"]),
	gaussianBlur: function(x = 0, y = x) {
		this.attr("stdDeviation", x + " " + y);
	},
	image: function(src) {
		this.attr("href", src, namespaces.xlink);
	},
	morphology: getAttrSetter(["operator", "radius"]),
	offset: getAttrSetter(["dx", "dy"]),
	specularLighting: getAttrSetter([
		"surfaceScale",
		"lightingColor",
		"diffuseConstant",
		"specularExponent",
		"kernelUnitLength"
	]),
	tile: getAttrSetter([]),
	turbulence: getAttrSetter([
		"baseFrequency",
		"numOctaves",
		"seed",
		"stitchTiles",
		"type"
	])
};
[
	"blend",
	"colorMatrix",
	"componentTransfer",
	"composite",
	"convolveMatrix",
	"diffuseLighting",
	"displacementMap",
	"dropShadow",
	"flood",
	"gaussianBlur",
	"image",
	"merge",
	"morphology",
	"offset",
	"specularLighting",
	"tile",
	"turbulence"
].forEach((effect) => {
	const name = utils.capitalize(effect);
	const fn = updateFunctions[effect];
	Filter[name + "Effect"] = class extends Effect {
		constructor(node) {
			super(nodeOrNew("fe" + name, node), node);
		}
		update(args) {
			fn.apply(this, args);
			return this;
		}
	};
	Filter.prototype[effect] = wrapWithAttrCheck(function(fn, ...args) {
		const effect = new Filter[name + "Effect"]();
		if (fn == null) return this.put(effect);
		if (typeof fn === "function") fn.call(effect, effect);
		else args.unshift(fn);
		return this.put(effect).update(args);
	});
});
extend(Filter, {
	merge(arrayOrFn) {
		const node = this.put(new Filter.MergeEffect());
		if (typeof arrayOrFn === "function") {
			arrayOrFn.call(node, node);
			return node;
		}
		(arrayOrFn instanceof Array ? arrayOrFn : [...arguments]).forEach((child) => {
			if (child instanceof Filter.MergeNode) node.put(child);
			else node.mergeNode(child);
		});
		return node;
	},
	componentTransfer(components = {}) {
		const node = this.put(new Filter.ComponentTransferEffect());
		if (typeof components === "function") {
			components.call(node, node);
			return node;
		}
		if (!components.r && !components.g && !components.b && !components.a) {
			const temp = components;
			components = {
				r: temp,
				g: temp,
				b: temp,
				a: temp
			};
		}
		for (const c in components) node.add(new Filter["Func" + c.toUpperCase()](components[c]));
		return node;
	}
});
[
	"distantLight",
	"pointLight",
	"spotLight",
	"mergeNode",
	"FuncR",
	"FuncG",
	"FuncB",
	"FuncA"
].forEach((child) => {
	const name = utils.capitalize(child);
	Filter[name] = class extends Effect {
		constructor(node) {
			super(nodeOrNew("fe" + name, node), node);
		}
	};
});
[
	"funcR",
	"funcG",
	"funcB",
	"funcA"
].forEach(function(c) {
	const _class = Filter[utils.capitalize(c)];
	const fn = wrapWithAttrCheck(function() {
		return this.put(new _class());
	});
	Filter.ComponentTransferEffect.prototype[c] = fn;
});
[
	"distantLight",
	"pointLight",
	"spotLight"
].forEach((light) => {
	const _class = Filter[utils.capitalize(light)];
	const fn = wrapWithAttrCheck(function() {
		return this.put(new _class());
	});
	Filter.DiffuseLightingEffect.prototype[light] = fn;
	Filter.SpecularLightingEffect.prototype[light] = fn;
});
extend(Filter.MergeEffect, { mergeNode(_in) {
	return this.put(new Filter.MergeNode()).attr("in", _in);
} });
extend(Defs, { filter: function(block) {
	const filter = this.put(new Filter());
	if (typeof block === "function") block.call(filter, filter);
	return filter;
} });
extend(Container, { filter: function(block) {
	return this.defs().filter(block);
} });
extend(Element, {
	filterWith: function(block) {
		const filter = block instanceof Filter ? block : this.defs().filter(block);
		return this.attr("filter", filter);
	},
	unfilter: function(remove) {
		const filter = this.filterer();
		this.attr("filter", null);
		if (remove && filter) filter.remove();
		return this;
	},
	filterer() {
		return this.reference("filter");
	}
});
extend(Effect, {
	blend: function(in2, mode) {
		return this.parent() && this.parent().blend(this, in2, mode);
	},
	colorMatrix: function(type, values) {
		return this.parent() && this.parent().colorMatrix(type, values).in(this);
	},
	componentTransfer: function(components) {
		return this.parent() && this.parent().componentTransfer(components).in(this);
	},
	composite: function(in2, operator) {
		return this.parent() && this.parent().composite(this, in2, operator);
	},
	convolveMatrix: function(matrix) {
		return this.parent() && this.parent().convolveMatrix(matrix).in(this);
	},
	diffuseLighting: function(surfaceScale, lightingColor, diffuseConstant, kernelUnitLength) {
		return this.parent() && this.parent().diffuseLighting(surfaceScale, lightingColor, diffuseConstant, kernelUnitLength).in(this);
	},
	displacementMap: function(in2, scale, xChannelSelector, yChannelSelector) {
		return this.parent() && this.parent().displacementMap(this, in2, scale, xChannelSelector, yChannelSelector);
	},
	dropShadow: function(x, y, stdDeviation) {
		return this.parent() && this.parent().dropShadow(this, x, y, stdDeviation).in(this);
	},
	flood: function(color, opacity) {
		return this.parent() && this.parent().flood(color, opacity);
	},
	gaussianBlur: function(x, y) {
		return this.parent() && this.parent().gaussianBlur(x, y).in(this);
	},
	image: function(src) {
		return this.parent() && this.parent().image(src);
	},
	merge: function(arg) {
		arg = arg instanceof Array ? arg : [...arg];
		return this.parent() && this.parent().merge(this, ...arg);
	},
	morphology: function(operator, radius) {
		return this.parent() && this.parent().morphology(operator, radius).in(this);
	},
	offset: function(dx, dy) {
		return this.parent() && this.parent().offset(dx, dy).in(this);
	},
	specularLighting: function(surfaceScale, lightingColor, diffuseConstant, specularExponent, kernelUnitLength) {
		return this.parent() && this.parent().specularLighting(surfaceScale, lightingColor, diffuseConstant, specularExponent, kernelUnitLength).in(this);
	},
	tile: function() {
		return this.parent() && this.parent().tile().in(this);
	},
	turbulence: function(baseFrequency, numOctaves, seed, stitchTiles, type) {
		return this.parent() && this.parent().turbulence(baseFrequency, numOctaves, seed, stitchTiles, type).in(this);
	}
});
extend(Filter.MergeEffect, { in: function(effect) {
	if (effect instanceof Filter.MergeNode) this.add(effect, 0);
	else this.add(new Filter.MergeNode().in(effect), 0);
	return this;
} });
extend([
	Filter.CompositeEffect,
	Filter.BlendEffect,
	Filter.DisplacementMapEffect
], { in2: function(effect) {
	if (effect == null) {
		const in2 = this.attr("in2");
		return this.parent() && this.parent().find(`[result="${in2}"]`)[0] || in2;
	}
	return this.attr("in2", effect);
} });
Filter.filter = { sepiatone: [
	.343,
	.669,
	.119,
	0,
	0,
	.249,
	.626,
	.13,
	0,
	0,
	.172,
	.334,
	.111,
	0,
	0,
	0,
	0,
	0,
	1,
	0
] };

//#endregion
export { Filter as default };