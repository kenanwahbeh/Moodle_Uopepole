# استخراج المقررات من قسم recentlyaccessedcourses
courses = soup.find_all("a", href=lambda x: x and "course/view.php?id=" in x)

for course in courses:
    print(course.text.strip(), "=>", course["href"])