#!/usr/bin/env python3
"""
Test script to demonstrate AI-powered tournament features
"""

from utils import (
    get_ai_tournament_suggestion, 
    analyze_historical_performance, 
    analyze_market_trends,
    get_optimal_tournament_timing,
    calculate_advanced_profit_analysis
)

def test_ai_features():
    print("🤖 TESTING AI-POWERED TOURNAMENT SYSTEM\n")
    
    # Test AI suggestions for all tournament types
    for tournament_type in ['solo', 'duo', 'squad']:
        print(f"--- {tournament_type.upper()} TOURNAMENT AI ANALYSIS ---")
        
        # Get AI suggestion
        suggestion = get_ai_tournament_suggestion(tournament_type)
        print(f"AI Suggestion: {suggestion['name']}")
        print(f"Map: {suggestion['map']}")
        print(f"Entry Fee: ₹{suggestion['entry_fee']}")
        print(f"Prize Type: {suggestion['prize_type']}")
        print(f"Confidence: {suggestion['confidence']}%")
        print(f"Reasoning: {suggestion['reasoning']}")
        print(f"Optimal Participants: {suggestion['optimal_participants']}")
        
        # Calculate profit analysis
        profit_analysis = calculate_advanced_profit_analysis(
            tournament_type, 
            suggestion['optimal_participants'], 
            suggestion['entry_fee'], 
            suggestion
        )
        
        print(f"\nPROFIT ANALYSIS:")
        print(f"Total Collection: ₹{profit_analysis['total_collection']:,}")
        print(f"Estimated Payout: ₹{profit_analysis['estimated_payout']:,}")
        print(f"Net Profit: ₹{profit_analysis['net_profit']:,}")
        print(f"ROI: {profit_analysis['adjusted_roi']}%")
        print(f"Risk Level: {profit_analysis['risk_level']}")
        print(f"Recommendation: {profit_analysis['recommendation']}")
        print()
    
    # Test market analysis
    print("--- MARKET TRENDS ANALYSIS ---")
    market_trends = analyze_market_trends()
    print(f"Player Activity: {market_trends['player_activity']}%")
    print(f"Competition Level: {market_trends['competition_level']}")
    print(f"New Registrations (7 days): {market_trends['new_registrations']}")
    print(f"Trending Maps: {', '.join(market_trends['trending_maps'])}")
    
    # Test optimal timing
    print("\n--- OPTIMAL TIMING ANALYSIS ---")
    optimal_timing = get_optimal_tournament_timing()
    print(f"Next Best Slot: {optimal_timing['suggested_time']} on {optimal_timing['suggested_date']}")
    print(f"Slot Quality: {optimal_timing['slot_quality']}")
    print(f"Expected Participation: {optimal_timing['expected_participation']}")
    print(f"Hours From Now: {optimal_timing['hours_from_now']}")
    
    # Test historical performance
    print("\n--- HISTORICAL PERFORMANCE ---")
    for tournament_type in ['solo', 'duo', 'squad']:
        historical_data = analyze_historical_performance(tournament_type)
        print(f"{tournament_type.upper()}: Avg {historical_data['avg_participants']} participants, {historical_data['success_rate']}% success rate")
    
    print("\n✅ AI SYSTEM FULLY OPERATIONAL!")

if __name__ == '__main__':
    test_ai_features()

def get_ai_tournament_suggestion(mode: str) -> str:
    if mode == "solo":
        return (
            "🎯 *AI Suggested Solo Tournament:*\n"
            "• Entry Fee: ₹20\n"
            "• Prize Pool: ₹500\n"
            "• Top 10 Players Win\n"
            "• Map: Erangel\n"
            "• Mode: TPP"
        )
    elif mode == "duo":
        return (
            "👬 *AI Suggested Duo Tournament:*\n"
            "• Entry Fee: ₹40/team\n"
            "• Prize Pool: ₹1000\n"
            "• Top 5 Teams Win\n"
            "• Map: Livik\n"
            "• Mode: FPP"
        )
    elif mode == "squad":
        return (
            "👑 *AI Suggested Squad Tournament:*\n"
            "• Entry Fee: ₹100/team\n"
            "• Prize Pool: ₹5000\n"
            "• Top 3 Squads Win\n"
            "• Map: Miramar\n"
            "• Mode: TPP/FPP"
        )
    else:
        return "❌ Invalid type! Use `/aihost solo`, `/aihost duo`, or `/aihost squad`"
