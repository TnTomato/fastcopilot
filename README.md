# FastCopilot

## Example

```python
from fastcopilot import Copilot


copilot = Copilot(api_key="your-api-key")

while True:
    ipt = input("Me: ")
    reply = copilot.run(ipt.strip())
    print(reply)
```

### For asyncio
```python
import asyncio

from fastcopilot import Copilot


copilot = Copilot(api_key="your-api-key")

def main():
    while True:
        ipt = input("Me: ")
        reply = await copilot.arun(ipt.strip())
        print(reply)

if __name__ == '__main__':
    asyncio.run(main())
```