import os
from card_generator import create_player_card
import logging

def test_card_generation():
    # Setup test parameters
    test_output_dir = os.path.join(os.path.dirname(__file__), 'test_output')
    os.makedirs(test_output_dir, exist_ok=True)
    
    test_cases = [
        {
            'name': 'test_basic',
            'player_name': 'John Doe',
            'nickname': 'Johnny',
            'role': 'All-Rounder',
            'photo_path': None,
            'expected_success': True
        },
        {
            'name': 'test_no_nickname',
            'player_name': 'Jane Smith',
            'nickname': None,
            'role': 'Left-Hand Batter',
            'photo_path': None,
            'expected_success': True
        },
        {
            'name': 'test_long_role',
            'player_name': 'Mike Johnson',
            'nickname': 'MJ',
            'role': 'Left-Hand Batter | Right-Arm Bowler | All-Rounder',
            'photo_path': None,
            'expected_success': True
        }
    ]
    
    for test_case in test_cases:
        output_path = os.path.join(test_output_dir, f"{test_case['name']}.png")
        
        print(f"\nRunning test: {test_case['name']}")
        success = create_player_card(
            player_name=test_case['player_name'],
            nickname=test_case['nickname'],
            role=test_case['role'],
            photo_path=test_case['photo_path'],
            output_path=output_path
        )
        
        if success == test_case['expected_success']:
            print(f"✓ Test passed: {test_case['name']}")
            if success:
                print(f"  Card created at: {output_path}")
        else:
            print(f"✗ Test failed: {test_case['name']}")
            print(f"  Expected: {test_case['expected_success']}, Got: {success}")

if __name__ == '__main__':
    # Set logging level to INFO for more detailed output
    logging.basicConfig(level=logging.INFO)
    test_card_generation()