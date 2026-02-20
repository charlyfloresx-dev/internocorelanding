using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Http.Features;

var builder = WebApplication.CreateBuilder(args);

// Add services to the container.

builder.Services.AddControllers();
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

builder.Services.Configure<Interno.Domain.Helpers.AppSettings>(builder.Configuration.GetSection("AppSettings"));

builder.Services.AddDbContext<Interno.Gym.Models.GymContext>(
    dbContextOptions => dbContextOptions
        .UseMySql(builder.Configuration.GetSection("AppSettings")["Database"]?.ToString(), new MySqlServerVersion(new Version(8, 0, 33)))
        // The following three options help with debugging, but should
        // be changed or removed for production.
        .LogTo(Console.WriteLine, LogLevel.Information)
        .EnableSensitiveDataLogging()
        .EnableDetailedErrors()
);

builder.Services.AddEndpointsApiExplorer();
builder.Services.AddSwaggerGen();

var MyAllowSpecificOrigins = "_myAllowSpecificOrigins";

builder.Services.AddCors(options =>
{
    options.AddPolicy(name: MyAllowSpecificOrigins, policy => { policy.WithOrigins("*").AllowAnyHeader().AllowAnyMethod(); });
});

builder.Services.AddControllers().AddNewtonsoftJson();

builder.Services.Configure<FormOptions>(o => { o.ValueLengthLimit = int.MaxValue; o.MultipartBodyLengthLimit = long.MaxValue; o.MemoryBufferThreshold = int.MaxValue; });


var app = builder.Build();

// Configure the HTTP request pipeline.
if (app.Environment.IsDevelopment())
{
    app.UseSwagger();
    app.UseSwaggerUI();
}

app.UseHttpsRedirection();

app.UseAuthorization();

app.MapControllers();

app.Run();