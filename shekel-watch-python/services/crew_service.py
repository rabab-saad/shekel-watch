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


def compose_whatsapp_alert(currency_opps: list, stock_opps: list) -> str:
    """
    Agent 3 – WhatsApp Alert Composer.

    Takes lists of arbitrage opportunities (dicts) and produces a concise,
    emoji-rich WhatsApp message that a retail investor can act on immediately.

    currency_opps : list of dicts from get_currency_arbitrage (non-neutral rows)
    stock_opps    : list of dicts from get_watchlist_arbitrage (non-neutral rows)
    """
    if not currency_opps and not stock_opps:
        return "No active arbitrage opportunities at this time."

    try:
        llm = LLM(
            model="gpt-4o-mini",
            api_key=get("OPENAI_API_KEY"),
        )

        composer = Agent(
            role="WhatsApp Alert Composer",
            goal=(
                "Write a short, clear WhatsApp alert message about arbitrage opportunities "
                "that an investor can read in under 30 seconds and act on immediately."
            ),
            backstory=(
                "You are a financial alert system for Israeli retail investors. "
                "Your messages are concise, use relevant emojis, and always include "
                "the specific numbers (gap %, prices) so the investor can verify the opportunity. "
                "You never give financial advice — you present facts and let the user decide."
            ),
            llm=llm,
            verbose=False,
        )

        opp_text = ""
        if currency_opps:
            opp_text += "CURRENCY ARBITRAGE:\n"
            for o in currency_opps:
                opp_text += (
                    f"  • {o.get('Pair')}: direct={o.get('Direct (X→ILS)')}, "
                    f"via USD={o.get('Via USD (X→$→₪)')}, gap={o.get('Gap %')}%, "
                    f"signal={o.get('Signal')}\n"
                )
        if stock_opps:
            opp_text += "\nSTOCK ARBITRAGE (Dual-listed):\n"
            for o in stock_opps:
                opp_text += (
                    f"  • {o.get('Stock')}: TASE=₪{o.get('TASE (₪)')}, "
                    f"NYSE equiv=₪{o.get('NYSE in ₪')} (${o.get('NYSE (USD)')}), "
                    f"gap={o.get('Gap %')}%, signal={o.get('Signal')}\n"
                )

        compose_task = Task(
            description=(
                f"Write a WhatsApp alert for the following arbitrage opportunities:\n\n"
                f"{opp_text}\n"
                "Rules:\n"
                "- Max 200 words\n"
                "- Start with ⚡ SHEKEL-WATCH ALERT ⚡\n"
                "- List each opportunity clearly with its gap % and recommended action\n"
                "- End with a disclaimer: 'Not financial advice. Verify before trading.'\n"
                "- Use emojis to make it scannable"
            ),
            expected_output="A WhatsApp-ready alert message under 200 words.",
            agent=composer,
        )

        crew = Crew(agents=[composer], tasks=[compose_task], verbose=False)
        result = crew.kickoff()
        return str(result)

    except Exception as e:
        # Fallback: plain text alert without AI
        lines = ["⚡ SHEKEL-WATCH ALERT ⚡\n"]
        if currency_opps:
            lines.append("💱 Currency Arbitrage:")
            for o in currency_opps:
                lines.append(f"  • {o.get('Pair')}: gap {o.get('Gap %')}% — {o.get('Signal')}")
        if stock_opps:
            lines.append("\n📈 Stock Arbitrage:")
            for o in stock_opps:
                lines.append(f"  • {o.get('Stock')}: gap {o.get('Gap %')}% — {o.get('Signal')}")
        lines.append("\n⚠️ Not financial advice. Verify before trading.")
        return "\n".join(lines)
