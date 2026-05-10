"""
Tax engine abstractions for multi-regime support.

Each legal form (micro-entrepreneur, EI au réel, EURL, SASU, SAS) has its own
calculation rules for cotisations sociales, CFP, IR/IS, dividends, etc.
This module exposes a `TaxEngine` interface and concrete implementations,
selectable via `get_engine(legal_form)`.

The numbers used (cotisation rates, IS thresholds, etc.) are reasonable
defaults for France 2024. Some are configurable per-profile (cotisation_rate,
tns_cotisations_rate, foyer_tmi…). The IS bracket (15 %/25 % at 42 500 €) is
hard-coded since it is set by law.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass


# Annual French legal IS thresholds (impôt sur les sociétés)
_IS_THRESHOLD_YEARLY = 42500.0
_IS_RATE_LOW = 0.15
_IS_RATE_HIGH = 0.25

# Default cotisations rates for assimilé-salarié (SASU/SAS président).
# Employer charges ~45 % of gross, employee charges ~22 % of gross.
# Total social cost = gross × (employer + employee) = gross × 0.67.
_ASSIMILE_SALARIE_EMPLOYER_RATE = 0.45
_ASSIMILE_SALARIE_EMPLOYEE_RATE = 0.22
_ASSIMILE_SALARIE_TOTAL_RATE = _ASSIMILE_SALARIE_EMPLOYER_RATE + _ASSIMILE_SALARIE_EMPLOYEE_RATE

# Flat tax (PFU) on dividends: 12.8 % IR + 17.2 % PS = 30 %
_DIVIDENDS_FLAT_TAX = 0.30


def _period_factor(period: str) -> float:
    """Return the multiplier from yearly amount to one period (e.g. month → 1/12)."""
    if period == "month":
        return 1 / 12
    if period == "quarter":
        return 1 / 4
    return 1.0  # year


def _annualize(amount: float, period: str) -> float:
    """Scale a per-period amount to its yearly equivalent."""
    return amount / _period_factor(period)


def _scale_yearly_to_period(yearly: float, period: str) -> float:
    return yearly * _period_factor(period)


def _compute_is(benefice_period: float, period: str) -> float:
    """Compute corporate tax (IS) on a per-period benefice using the legal bracket.

    We annualize the benefice, apply the bracket, then scale back. Keeps the
    threshold logic correct across periods.
    """
    if benefice_period <= 0:
        return 0.0
    benefice_year = _annualize(benefice_period, period)
    is_year = (
        min(benefice_year, _IS_THRESHOLD_YEARLY) * _IS_RATE_LOW
        + max(0.0, benefice_year - _IS_THRESHOLD_YEARLY) * _IS_RATE_HIGH
    )
    return _scale_yearly_to_period(is_year, period)


@dataclass
class PeriodInput:
    """All inputs needed to compute a tax breakdown for one period."""

    turnover: float                      # Chiffre d'affaires encaissé
    declared_turnover: float             # Part du CA marquée comme « comptabilisé »
    expenses: float                      # Charges (dépenses pro encaissées)
    period: str                          # 'month' | 'quarter' | 'year'


@dataclass
class TaxBreakdown:
    """Detailed view of all prélèvements for one period."""

    period: str
    turnover: float
    deductible_expenses: float
    benefice_imposable: float | None
    cotisations_sociales: float
    cfp: float
    ir_versement_liberatoire: float | None
    ir_classique_estime: float | None
    impot_societes: float | None
    dividendes_taxes: float | None
    total_prelevements: float
    net_after_taxes: float
    notes: list[str]
    # Incorporated entities (SASU/SAS/EURL-IS) only — net salary received by the dirigeant
    net_salary: float | None = None
    # What the user pockets personally for the period — comparable across regimes.
    # = net_after_taxes for non-incorporated regimes (the user IS the company).
    # = (net_salary − personal IR) + (dividends − dividend tax) for incorporated.
    personal_take_home: float = 0.0


class TaxEngine(ABC):
    """Base class for all regime-specific tax computation engines."""

    legal_form: str = ""

    @abstractmethod
    def compute(self, period: PeriodInput, profile: dict) -> TaxBreakdown:
        ...


# ── Micro-entrepreneur ──────────────────────────────────────────────────────


_MICRO_DEFAULTS_BY_ACTIVITY: dict[str, dict[str, float]] = {
    "vente":            {"cfp": 0.001, "vl": 0.010, "abattement": 0.71},
    "commercant":       {"cfp": 0.001, "vl": 0.010, "abattement": 0.71},
    "services":         {"cfp": 0.003, "vl": 0.017, "abattement": 0.50},
    "artisan":          {"cfp": 0.003, "vl": 0.017, "abattement": 0.50},
    "liberal":          {"cfp": 0.002, "vl": 0.022, "abattement": 0.34},
    "location_meublee": {"cfp": 0.001, "vl": 0.010, "abattement": 0.50},
}


def _default_for(activity: str | None, key: str) -> float:
    if not activity:
        return _MICRO_DEFAULTS_BY_ACTIVITY["services"][key]
    return _MICRO_DEFAULTS_BY_ACTIVITY.get(activity, _MICRO_DEFAULTS_BY_ACTIVITY["services"])[key]


class MicroEngine(TaxEngine):
    """Micro-entrepreneur: cotisations and IR computed as a percentage of CA encaissé."""

    legal_form = "micro"

    def compute(self, period: PeriodInput, profile: dict) -> TaxBreakdown:
        notes: list[str] = []
        activity = profile.get("activity_type") or "services"

        cot_rate = (profile.get("cotisation_rate") or 21.2) / 100
        cotisations = period.declared_turnover * cot_rate

        cfp_rate = profile.get("cfp_rate")
        cfp_rate = cfp_rate / 100 if cfp_rate is not None else _default_for(activity, "cfp")
        cfp = period.declared_turnover * cfp_rate

        ir_vl: float | None = None
        ir_class: float | None = None
        if profile.get("versement_liberatoire_enabled"):
            vl_rate = profile.get("versement_liberatoire_rate")
            vl_rate = vl_rate / 100 if vl_rate is not None else _default_for(activity, "vl")
            ir_vl = period.declared_turnover * vl_rate
        else:
            tmi = profile.get("foyer_tmi")
            if tmi is not None:
                abattement = profile.get("ir_abattement_rate")
                abattement = abattement / 100 if abattement is not None else _default_for(activity, "abattement")
                imposable = period.declared_turnover * (1 - abattement)
                ir_class = imposable * (tmi / 100)
            else:
                notes.append(
                    "IR classique non estimé : renseignez votre TMI (taux marginal d'imposition) dans le profil."
                )

        total = cotisations + cfp + (ir_vl or 0) + (ir_class or 0)
        net = period.turnover - total

        return TaxBreakdown(
            period=period.period,
            turnover=period.turnover,
            deductible_expenses=0.0,
            benefice_imposable=None,
            cotisations_sociales=cotisations,
            cfp=cfp,
            ir_versement_liberatoire=ir_vl,
            ir_classique_estime=ir_class,
            impot_societes=None,
            dividendes_taxes=None,
            total_prelevements=total,
            net_after_taxes=net,
            notes=notes,
            personal_take_home=net,
        )


# ── EI au régime réel & EURL au IR ───────────────────────────────────────────


class _RealRegimeIR(TaxEngine):
    """Shared logic for EI au réel and EURL à l'IR.

    Bénéfice = CA encaissé − charges déductibles. Cotisations TNS sur le
    bénéfice. IR au TMI sur le bénéfice (sans abattement forfaitaire).
    """

    def compute(self, period: PeriodInput, profile: dict) -> TaxBreakdown:
        notes: list[str] = []
        benefice = max(0.0, period.turnover - period.expenses)

        tns_rate = (profile.get("tns_cotisations_rate") or 45.0) / 100
        cotisations = benefice * tns_rate

        ir_class: float | None = None
        tmi = profile.get("foyer_tmi")
        if tmi is not None:
            ir_class = benefice * (tmi / 100)
        else:
            notes.append("IR non estimé : renseignez votre TMI dans le profil.")

        total = cotisations + (ir_class or 0)
        net = period.turnover - period.expenses - total

        return TaxBreakdown(
            period=period.period,
            turnover=period.turnover,
            deductible_expenses=period.expenses,
            benefice_imposable=benefice,
            cotisations_sociales=cotisations,
            cfp=0.0,
            ir_versement_liberatoire=None,
            ir_classique_estime=ir_class,
            impot_societes=None,
            dividendes_taxes=None,
            total_prelevements=total,
            net_after_taxes=net,
            notes=notes,
            personal_take_home=net,
        )


class EIRealEngine(_RealRegimeIR):
    legal_form = "ei_reel"


# ── EURL: IR or IS option ────────────────────────────────────────────────────


class EURLEngine(TaxEngine):
    """EURL — dispatch to IR (real regime) or IS (corporate) based on profile.eurl_tax_option."""

    legal_form = "eurl"

    def compute(self, period: PeriodInput, profile: dict) -> TaxBreakdown:
        if (profile.get("eurl_tax_option") or "ir") == "is":
            return _ManagedSocietyEngine(is_assimile_salarie=False).compute(period, profile)
        return _RealRegimeIR().compute(period, profile)


# ── SASU / SAS: assimilé-salarié + IS + dividends ────────────────────────────


class _ManagedSocietyEngine(TaxEngine):
    """Common logic for incorporated entities under IS (SASU, SAS, EURL-IS).

    - Salaire mensuel brut (profile.salary_gross_monthly)
    - Cotisations sociales selon le statut :
        * assimilé-salarié (SASU/SAS) : ~67 % du brut versé (patronales + salariales)
        * gérant TNS (EURL-IS majoritaire) : tns_cotisations_rate du brut
    - Bénéfice = CA − charges − salaire brut − cotisations patronales
    - IS sur bénéfice (15 % jusqu'à 42 500 €/an, 25 % au-delà — pro-raté)
    - Dividendes (montant annuel prévu, profile.dividends_yearly) : flat tax 30 %
    """

    def __init__(self, is_assimile_salarie: bool = True):
        self.is_assimile_salarie = is_assimile_salarie

    def compute(self, period: PeriodInput, profile: dict) -> TaxBreakdown:
        notes: list[str] = []
        salary_monthly = profile.get("salary_gross_monthly") or 0.0
        salary_period = salary_monthly * (12 * _period_factor(period.period))

        if self.is_assimile_salarie:
            # SASU/SAS: split employer / employee charges, employee charges are
            # withheld from the gross salary (net = gross − employee).
            employer_charges = salary_period * _ASSIMILE_SALARIE_EMPLOYER_RATE
            employee_charges = salary_period * _ASSIMILE_SALARIE_EMPLOYEE_RATE
            cotisations = employer_charges + employee_charges
            net_salary = salary_period - employee_charges
        else:
            # EURL au IS: gérant majoritaire TNS. Cotisations payées par la société
            # par-dessus la rémunération ; le gérant reçoit l'intégralité de sa rému.
            tns_rate = (profile.get("tns_cotisations_rate") or 45.0) / 100
            employer_charges = salary_period * tns_rate
            cotisations = employer_charges
            net_salary = salary_period

        # Bénéfice imposable à l'IS : CA − charges − rémunération − cotisations société
        benefice = max(0.0, period.turnover - period.expenses - salary_period - employer_charges)
        is_value = _compute_is(benefice, period.period)

        dividends_year = profile.get("dividends_yearly") or 0.0
        dividends_period = _scale_yearly_to_period(dividends_year, period.period)
        dividends_taxes = dividends_period * _DIVIDENDS_FLAT_TAX

        # IR personnel sur la rémunération nette (approximation simple via TMI).
        ir_class: float | None = None
        tmi = profile.get("foyer_tmi")
        if salary_monthly > 0:
            if tmi is not None:
                ir_class = net_salary * (tmi / 100)
            else:
                notes.append(
                    "IR personnel non estimé : renseignez votre TMI dans le profil pour estimer l'impôt sur votre rémunération."
                )

        total = cotisations + is_value + dividends_taxes + (ir_class or 0)
        net = period.turnover - period.expenses - total

        if salary_monthly <= 0:
            notes.append("Pas de rémunération configurée : renseignez le salaire mensuel brut dans le profil pour un calcul plus précis.")
        if dividends_year <= 0:
            notes.append("Pas de dividendes prévus : si vous comptez en distribuer, renseignez le montant annuel dans le profil.")

        # Personal take-home: what the dirigeant pockets after all personal taxes.
        personal = (net_salary - (ir_class or 0)) + (dividends_period - dividends_taxes)

        return TaxBreakdown(
            period=period.period,
            turnover=period.turnover,
            deductible_expenses=period.expenses,
            benefice_imposable=benefice,
            cotisations_sociales=cotisations,
            cfp=0.0,
            ir_versement_liberatoire=None,
            ir_classique_estime=ir_class,
            impot_societes=is_value,
            dividendes_taxes=dividends_taxes,
            total_prelevements=total,
            net_after_taxes=net,
            notes=notes,
            net_salary=net_salary if salary_monthly > 0 else None,
            personal_take_home=personal,
        )


class SASUEngine(_ManagedSocietyEngine):
    legal_form = "sasu"

    def __init__(self):
        super().__init__(is_assimile_salarie=True)


class SASEngine(_ManagedSocietyEngine):
    legal_form = "sas"

    def __init__(self):
        super().__init__(is_assimile_salarie=True)


_ENGINES: dict[str, type[TaxEngine]] = {
    "micro":   MicroEngine,
    "ei_reel": EIRealEngine,
    "eurl":    EURLEngine,
    "sasu":    SASUEngine,
    "sas":     SASEngine,
}


def get_engine(legal_form: str | None) -> TaxEngine:
    """Resolve the engine for a given legal form. Falls back to MicroEngine."""
    cls = _ENGINES.get(legal_form or "micro", MicroEngine)
    return cls()
