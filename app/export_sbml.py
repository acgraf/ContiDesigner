import libsbml
from .conti_reactions import reaction_definitions_onestage
from .conti_reactions import reaction_definitions_cascade


# %%
def create_sbml_basics(model, n_stages=2):
    # Create SBML document and model
    label = "onestage" if n_stages == 1 else "cascade"
    doc = libsbml.SBMLDocument(3, 2)  # SBML Level 3 Version 2
    sbml_model = doc.createModel()
    sbml_model.setId(f"{label}_conti_model")
    # define compartments == distinct physical spaces
    for i in range(1, n_stages + 1):
        c = sbml_model.createCompartment()
        c.setId(f"Reactor{i}")
        c.setConstant(True)
        Vol = (
            getattr(model, f"V_{label}", 1.0)
            if label == "onestage"
            else getattr(model, f"V{i}", 1.0)
        )
        c.setSize(Vol)

        # Pick the right initial state vector (growth vs production)
        init = (
            model.growth_initial_state
            if i == 1
            else getattr(model, f"prod_initial_state", model.growth_initial_state)
        )

        prefix = f"s{i}"
        for name, val in zip(["X", "S", "P"], init):
            s = sbml_model.createSpecies()
            s.setId(f"{name}_{prefix}")
            s.setCompartment(c.getId())
            s.setInitialConcentration(val)
            s.setBoundaryCondition(False)  # species is dynamic, not fixed
            s.setHasOnlySubstanceUnits(False)  # species is tracked in conc units
            s.setSubstanceUnits("g_per_L")
            s.setConstant(False)  # is not constant

    # add parameters
    for k, v in model.numeric_input_params.items():
        p = sbml_model.createParameter()
        p.setId(str(k))  # parameter name is ID
        # print(v)
        p.setValue(float(v))
        p.setConstant(True)  # all parameters are constant

    return doc, sbml_model


def add_reactions_to_model(model, sbml_model, reaction_definitions):

    def normalize_rate(rate_str):
        r = rate_str.strip()
        # print(r)
        is_negative = False
        if r.startswith("-"):
            is_negative = True
            r = r[1:].lstrip()
        return is_negative, r

    inhib_factors = []

    if model.is_substrate_inhibited:
        inhib_factors.append("S_s1 / (Ks + S_s1 + S_s1^2 / Ki)")
    else:  # monod is already incorporated in substrate limitation
        inhib_factors.append("(S_s1 / (Ks + S_s1))")
    if model.is_product_inhibited:
        inhib_factors.append("(1 - P_s1 / pmax)^n1")
    if model.is_biomass_inhibited:
        inhib_factors.append("(1 - X_s1 / xmax)^n2")

    inhibition_expression = " * ".join(inhib_factors)

    possible_mods = ["X_s1", "X_s2", "S_s1", "S_s2", "P_s1", "P_s2"]
    # iterate over all species and their reactions
    for species_key, rxn_list in reaction_definitions.items():
        for rxn in rxn_list:
            rid = rxn["id"]
            raw_rate = rxn["rate"]
            is_negative, flux_expr = normalize_rate(raw_rate)

            if "mu_max" in flux_expr:  # growth reactions
                flux_expr = flux_expr.replace(
                    "mu_max", f"(mu_max * {inhibition_expression})"
                )

            # create the reaction object
            r = sbml_model.createReaction()
            r.setId(rid)
            r.setReversible(False)

            if is_negative:
                # consumption / outflow
                reactant = r.createReactant()
                reactant.setSpecies(species_key)
                reactant.setStoichiometry(1.0)
                reactant.setConstant(True)
            else:
                # production / inflow
                product = r.createProduct()
                product.setSpecies(species_key)
                product.setStoichiometry(1.0)
                product.setConstant(True)

            for mod_name in possible_mods:
                if mod_name != species_key and (mod_name in flux_expr):
                    mod = r.createModifier()
                    mod.setSpecies(mod_name)

            # Create kinetic law (rate formula)
            kl = r.createKineticLaw()
            try:
                kl.setMath(libsbml.parseL3Formula(flux_expr))
            except Exception as e:
                # reaction id and expression if parse fails
                raise RuntimeError(
                    f"Failed to parse rate for reaction {rid}: '{flux_expr}'\n{e}"
                )

    return sbml_model


# %%
def export_contimodel_to_sbml(model, n_stages=2):
    """Return SBML as string instead of writing to file."""
    reaction_definitions = (
        reaction_definitions_onestage if n_stages == 1 else reaction_definitions_cascade
    )
    doc, sbml_model = create_sbml_basics(model, n_stages)
    sbml_model = add_reactions_to_model(model, sbml_model, reaction_definitions)
    sbml_str = libsbml.writeSBMLToString(doc)
    return sbml_str
