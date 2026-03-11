from crewai import Agent, Task, Crew, LLM
from services.config import get


def get_market_summary(market_data: str, currency_data: str) -> str:
    """
    Uses two CrewAI agents to analyse market data and produce a summary.
    Agent 1 – Market Analyst: spots trends and risks.
    Agent 2 – Financial Reporter: writes the investor-facing summary.
    """
    try:
        llm = LLM(
            model="gpt-4o-mini",
            api_key=get("OPENAI_API_KEY"),
        )

        analyst = Agent(
            role="Market Data Analyst",
            goal="Analyse Israeli and global market data and identify key trends",
            backstory=(
                "You are a senior financial analyst with 20 years of experience "
                "specialising in the Tel Aviv Stock Exchange and global macro trends. "
                "You use data-driven insights to spot opportunities and risks."
            ),
            llm=llm,
            verbose=False,
        )

        reporter = Agent(
            role="Financial Reporter",
            goal="Write concise, clear market summaries for retail investors",
            backstory=(
                "You are a financial journalist writing for an Israeli retail audience. "
                "You translate complex market movements into plain language that anyone "
                "can understand, focusing on what matters for day-to-day investing."
            ),
            llm=llm,
            verbose=False,
        )

        analyse_task = Task(
            description=(
                f"Analyse the following live market data:\n\n"
                f"MARKET INDICES:\n{market_data}\n\n"
                f"CURRENCY RATES:\n{currency_data}\n\n"
                "Identify: (1) major index movements, (2) USD/ILS trend, "
                "(3) notable currency moves, (4) key risks for Israeli investors."
            ),
            expected_output="Bullet-point analysis covering the four areas above.",
            agent=analyst,
        )

        report_task = Task(
            description=(
                "Based on the analyst's findings write a 3–4 sentence market summary "
                "suitable for Israeli retail investors. End with one clear, actionable insight."
            ),
            expected_output="A 3–4 sentence market summary with one actionable insight.",
            agent=reporter,
            context=[analyse_task],
        )

        crew = Crew(
            agents=[analyst, reporter],
            tasks=[analyse_task, report_task],
            verbose=False,
        )

        result = crew.kickoff()
        return str(result)

    except Exception as e:
        return f"AI summary unavailable: {e}"
