import sys
import asyncio

sys.path.insert(0, 'backend')
from scripts.real_dialogue_runner import RealDialogueRunner


async def main() -> None:
    runner = RealDialogueRunner()
    res = await runner.run_dialogue_simulation('WhatsApp 對話詐騙', 'elderly', max_turns=3)
    print({
        'keys': list(res.keys()) if isinstance(res, dict) else type(res).__name__,
        'outcome': res.get('outcome') if isinstance(res, dict) else None,
        'has_dialogue': bool(res.get('dialogue')) if isinstance(res, dict) else False,
    })


if __name__ == '__main__':
    asyncio.run(main())


