using System.ComponentModel.DataAnnotations;
using System.Text.RegularExpressions;

var builder = WebApplication.CreateBuilder(args);
var app = builder.Build();

app.UseStaticFiles();

// 🌟 1.1 GET /
app.MapGet("/", () => Results.Ok(new { message = "Добро пожаловать в моё приложение ASP.NET!" }));

// 🌟 1.2 HTML
app.MapGet("/html", () =>
{
    var path = Path.Combine(Directory.GetCurrentDirectory(), "index.html");
    return Results.File(path, "text/html");
});

// 🌟 1.3 POST /calculate
app.MapPost("/calculate", (CalcRequest req) =>
{
    return Results.Ok(new { result = req.num1 + req.num2 });
});

// 🌟 1.4 GET /users
var user = new User { Name = "Ваше Имя Фамилия", Id = 1 };
app.MapGet("/users", () => Results.Ok(user));

// 🌟 1.5 POST /user
app.MapPost("/user", (UserAgeDto u) =>
{
    bool isAdult = u.Age >= 18;
    return Results.Ok(new { name = u.Name, age = u.Age, is_adult = isAdult });
});

// 🌟 2.1 POST /feedback
var feedbacks = new List<Feedback>();
app.MapPost("/feedback", (Feedback f) =>
{
    feedbacks.Add(f);
    return Results.Ok(new { message = $"Feedback received. Thank you, {f.Name}." });
});

// 🌟 2.2 POST /feedback-validated
var feedbacksValidated = new List<FeedbackValidated>();
app.MapPost("/feedback-validated", (FeedbackValidated f) =>
{
    var badWords = new[] { "кринж", "рофл", "вайб" };

    foreach (var word in badWords)
    {
        if (Regex.IsMatch(f.Message.ToLower(), word))
        {
            return Results.UnprocessableEntity(new
            {
                error = "Использование недопустимых слов"
            });
        }
    }

    feedbacksValidated.Add(f);

    return Results.Ok(new { message = $"Спасибо, {f.Name}! Ваш отзыв сохранён." });
});

app.Run();


// ===== Models =====

record CalcRequest(int num1, int num2);

class User
{
    public string Name { get; set; } = "";
    public int Id { get; set; }
}

class UserAgeDto
{
    [Required]
    public string Name { get; set; } = "";

    [Range(0, 150)]
    public int Age { get; set; }
}

class Feedback
{
    [Required]
    public string Name { get; set; } = "";

    [Required]
    public string Message { get; set; } = "";
}

class FeedbackValidated
{
    [Required, MinLength(2), MaxLength(50)]
    public string Name { get; set; } = "";

    [Required, MinLength(10), MaxLength(500)]
    public string Message { get; set; } = "";
}