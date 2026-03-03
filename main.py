import asyncio
import path_finder 

async def main():
    start = input("Enter start page title: ")
    end = input("Enter end page title: ")

    check,path,links = await path_finder.finder(start,end)

    if check:
        print("PATH FOUND!!!!!!")
        print("-> ".join(path))

    else:
        print("PATH NOT FOUND")

    print(f"Check ended with a total of {links} checked.")

if __name__ == "__main__":
    asyncio.run(main())