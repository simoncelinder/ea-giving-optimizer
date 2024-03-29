import streamlit as st

# Relative import rather than module import for Streamlit to work
from helpers import (
    Config,
    run_linear_optimization,
    dict_values_to_thousands,
    dict_keys_to_thousands,
    check_valid_keys,
)


def constant_dict(current_age, life_exp_years, value) -> dict:
    result_dict = {}
    result_dict[current_age] = value
    result_dict[life_exp_years] = value
    return result_dict


# # # INTRO BEFORE FORM

st.title("""Explore how many lives you can save over your lifetime""")

ea_intro = ('https://www.youtube.com/watch?v=Diuv3XZQXyc')

st.write("This is a tool for exploring how many lives you can save over your own lifetime by giving to the most "
         "effective charities, and is inspired by the Effective Altruism movement, see: "
         "[Intro Video](%s)" % ea_intro)
st.write("More specifically, the purpose of the tool is to: ")
st.write("1) Hopefully get you inspired and motivated about saving more lives")
st.write("2) Explore how different assumptions impact *when* it is best to give to save most lives. "
         "Assumptions include salary at different age, return on the stock market, discount rate for waiting to give, "
         "and assumed future likelihood of *actually* giving. This might give rise to new "
         "ideas and perspectives on *when* it might be best to give to charity, and how to *ensure* it's done.")
st.caption("You can start with running the app with default values to get a sense of how it works!")

error_pretext = (
        'The run failed - this is generally due to incorrect format on the input data. You can always '
        'refresh the browser and start from working default values if needed. '
        'Error message from execution: '
    )


# # # TOGGLE MODES

if 'is_advanced' not in st.session_state:
    st.session_state.is_advanced = False


def switch_mode():
    st.session_state.is_advanced = not(st.session_state.is_advanced)


other_mode = 'Advanced' if not(st.session_state.is_advanced) else 'Basic'
st.button(f'Switch to {other_mode} mode', on_click=switch_mode)


# # # MAIN FORM

with st.form("input_assumptions", clear_on_submit=False):
    try:
        if st.session_state.is_advanced:
            save_qa_life_cost_k = st.slider(
                'Cost of saving a life at full quality in USD (e.g. roughly $3000 - $4500)',
                min_value=1000, max_value=6000, value=3500
            )/1000
            givewell_url = ('https://www.givewell.org/charities/top-charities')
            st.caption("Cost of saving a life at full quality can be estimated from randomized controlled trials, "
                       " see for example [GiveWell top charities](%s)" % givewell_url)

        else:
            save_qa_life_cost_k = 3500/1000

        if st.session_state.is_advanced:
            pre_post = st.selectbox('Will giving be pre-tax or post-tax?', ('Pre-tax', 'Post-tax'), index=1)
            is_giving_pretax = pre_post == 'Pre-tax'
        else:
            is_giving_pretax = False

        current_age = st.slider('Current age', min_value=15, max_value=150, value=30)
        if not st.session_state.is_advanced:
            age_of_retirement = st.slider(
                'Age of retirement',
                min_value=15, max_value=150, value=65
            )
        life_exp_years = st.slider('Life expectency', min_value=15, max_value=150, value=80)

        if st.session_state.is_advanced:
            current_savings_k = st.number_input(
                'Current savings [USD] after tax on profits',
                min_value=0, max_value=100000000000, value=0
            )/1000
        else:
            current_savings_k = 0

        return_rate_after_inflation_percent = st.slider('Stock market return rate after inflation [%]',
                                                    min_value=0.0, max_value=20.0, value=3.0, step=0.1)

        existential_risk_discount_rate_percent = st.slider('Discount rate for cost of existential risk '
                                                           'and global suffering [%]. ',
                                                           min_value=0.0, max_value=20.0, value=3.0, step=0.01)

        x_risk_derivation = ('https://forum.effectivealtruism.org/posts/3fmcNMrR8cktLnoYk/' +
                             'giving-now-vs-later-for-existential-risk-an-initial-approach')
        st.caption("Existential risk: Yearly discount rate for existential risk ≈ rate of extinction according to this "
                   "[x-risk derivation](%s)" % x_risk_derivation)
        st.caption("Global suffering: The discount rate might be related to the growth rate of developing countries, "
                   "suggesting it might be more expensive to save lives in the future.")

        if st.session_state.is_advanced:
            month_salary_k_per_age = st.text_input('Month salary in USD before tax at different sample ages as a dictionary '
                                                   '{age: salary}, they will be interpolated linearly',
                                                   value='{30: 4000, 40: 5000, 64: 5500, 66: 1500}')
            month_salary_k_per_age = dict_values_to_thousands(eval(month_salary_k_per_age))
        else:
            current_salary_k = st.number_input(
                'Current monthly salary in USD before tax',
                min_value=0, max_value=100000000000, value=3500
            )/1000
            month_salary_k_per_age = constant_dict(current_age, life_exp_years, value=current_salary_k)
            salary_increase_rate = st.slider('Salary increase [%] after inflation per year until retirement', min_value=0.0,
                                             max_value=50.0, value=2.0, step=0.5) / 100
            salary_after_retirement_k = st.number_input('Monthly income after retirement before tax in USD', min_value=0,
                                                     max_value=100000000000, value=1500) / 1000

            # TODO write unit test for this function
            for years, age in enumerate(
                range(min(month_salary_k_per_age.keys()) + 1, max(month_salary_k_per_age.keys()) + 1),
                start=1
            ):
                if age < age_of_retirement:
                    # Recursively apply interest on previous salary
                    month_salary_k_per_age[age] = round(month_salary_k_per_age[age-1] * (1 + salary_increase_rate), 2)
                else:
                    month_salary_k_per_age[age] = salary_after_retirement_k

        if st.session_state.is_advanced:
            month_req_cost_k_per_age = st.text_input(
                'Required cost of living per month per age as a dictionary '
                 '{age: cost}, they will be interpolated linearly',
                value='{30: 1800, 65: 2000, 66: 1100}'
            )
            month_req_cost_k_per_age = dict_values_to_thousands(eval(month_req_cost_k_per_age))
        else:
            cost_of_living_k = st.number_input(
                'Required cost of living per month in USD',
                min_value=0, max_value=100000000000, value=1000
            )/1000
            month_req_cost_k_per_age = constant_dict(current_age, life_exp_years, value=cost_of_living_k)

        default_tax = {0: 0.18, 2000: 0.2, 3000: 0.2, 4000: 0.225, 5000: 0.26, 6000: 0.3, 10000: 0.38}
        if st.session_state.is_advanced:
            share_tax_per_k_salary = st.text_input('Enter share total tax at ranges that cover at least min and '
                                                   'max salary per month above and preferably some points in between as a '
                                                   'dictionary, {salary: share_tax}, it will be interpolated linearly '
                                                   '(can be found in various salary-after-tax calculators online)',
                                                   value=f'{default_tax}')
            share_tax_per_k_salary = dict_keys_to_thousands(eval(share_tax_per_k_salary))
        else:
            share_tax_per_k_salary = default_tax
            share_tax_per_k_salary = dict_keys_to_thousands(share_tax_per_k_salary)

        if st.session_state.is_advanced:
            implementation_factor_per_age = st.text_input(
                'Enter expected implementation factor at different ages as a dictionary '
                'for example capturing leaking money to other causes like borrowing '
                'to relatives or passing away without testament or with legal '
                'requirements on inheritence etc. 1 => all money would go to charity '
                'when giving at that age, 0.5 => only 50% would go to charity etc.',
                value='{30: 1, 45: 1, 55: 0.90, 80: 0.5}'
            )
            implementation_factor_per_age = eval(implementation_factor_per_age)
        else:
            implementation_factor_per_age = constant_dict(current_age, life_exp_years, 1)

        has_reality_check = st.checkbox('Display underlying dataset')

        run = st.form_submit_button('Run giving optimizer!')

        st.caption("""The tool uses linear optimization to find the presumed 'optimal' giving at each age of your life to 
                      maximize number of lives saved, but needs to be combined with other perspectives. 
                      For example, recurring giving can help us stay engaged in doing good and inspire 
                      others to give, even out donation flows to charities etc.""")
        st.caption("When the stock market return is higher than the discount rate, the tool will generally favour "
                   "waiting to give, and conversely, when the discount rate is higher it will generally suggest giving "
                   "as much as possible straight way, though this also depends on assumptions about the implementation "
                   "factor when using Advanced mode.")

        giving_article = ('https://www.givingwhatwecan.org/blog/giving-effectively-by-hacking-your-psychology')
        st.caption(
            "For more on *psychological* mechanisms supporting effective giving, "
            "see article at Giving What We Can: [link](%s)" % giving_article
        )

        if st.session_state.is_advanced:
            st.caption("A limitation of the pre-tax giving implementation is that in reality, you probably have to donate this "
                       "money straight away. But you can more or less simulate this by setting the stock market return to 0.")
            code_git = ('https://github.com/simoncelinder/ea-giving-optimizer')
            st.caption("The code for this tool is available in git: [link](%s)" % code_git)

    except Exception as e:
        run = st.form_submit_button('Run giving optimizer!')
        st.write(f'{error_pretext}{e}')


# # # RUN OPTIMIZATION

if run:

    try:
        return_rate_after_inflation = return_rate_after_inflation_percent / 100
        existential_risk_discount_rate = existential_risk_discount_rate_percent / 100
        is_keys_ok = check_valid_keys(current_age, month_salary_k_per_age,
                                      month_req_cost_k_per_age, implementation_factor_per_age)

        if not is_keys_ok:
            st.write(f"Error: Current implementation does not support having current age be less than the "
                     f"lowest age of the input data dictionaries. Please update the dictionary to start at a lower age or "
                     f"set higher current age.")

        else:
            conf = Config(
                save_qa_life_cost_k=save_qa_life_cost_k,
                is_giving_pretax=is_giving_pretax,
                current_age=current_age,
                life_exp_years=life_exp_years,
                current_savings_k=current_savings_k,
                return_rate_after_inflation=return_rate_after_inflation,
                existential_risk_discount_rate=existential_risk_discount_rate,
                month_salary_k_per_age=month_salary_k_per_age,
                month_req_cost_k_per_age=month_req_cost_k_per_age,
                share_tax_per_k_salary=share_tax_per_k_salary,
                implementation_factor_per_age=implementation_factor_per_age
            )

            run_linear_optimization(conf)

            if (conf.df['disposable_for_giving'] < 0).any():
                st.write(
                    "<< Warning! >> There are negative values in disposable income left for giving. "
                    "While this should ideally be subtracted from total impact, it has not yet "
                    "been properly tested and can lead to unexpected effects."
                )

            st.write(f"Lives saved: {conf.lives_saved}, Sum given: {conf.sum_given_m :.2f} million USD ")

            # Lives saved as person symbols
            st.write(f'Lives saved at full quality of life visualized as people')
            st.write('👤 ' * conf.lives_saved)

            # Plotly graphs
            height, width = 300, 750
            st.plotly_chart(conf.plotly_summary_cum(height=height, width=width))
            st.plotly_chart(conf.plotly_summary(height=height, width=width))

            if has_reality_check:
                st.dataframe(conf.df.reset_index())

    except Exception as e:
        st.write(f'{error_pretext}{e}')
