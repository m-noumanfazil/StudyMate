from classes import ResumeRankingSystem, JobDescription
system = ResumeRankingSystem()

while True:
        print("\n===== Transparent Resume Ranking System =====")
        print("1. Insert Job Description")
        print("2. Insert Resumes")
        print("3. Calculate Scores")
        print("4. Show Sorted Results")
        print("5. Reset System")
        print("6. Exit")

        choice = input("Select an option: ")

        if choice == "1":
            if system.job is None:
                system.job = JobDescription()
            system.job.insert_text()

        elif choice == "2":
            system.insert_resumes()

        elif choice == "3":
            system.calculate_scores()

        elif choice == "4":
            system.show_sorted_results()

        elif choice == "5":
            system.reset_system()

        elif choice == "6":
            print("Exiting system.")
            break

        else:
            print("Invalid option. Try again.")

