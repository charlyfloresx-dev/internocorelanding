using Microsoft.EntityFrameworkCore;
using Microsoft.AspNetCore.Mvc.NewtonsoftJson;
using Microsoft.AspNetCore.Http.Features;
using Interno.Outset.Models;
using Interno.Outset.Helpers;

var builder = WebApplication.CreateBuilder(args);
// Add services to the container.

builder.Services.AddControllers();
// Learn more about configuring Swagger/OpenAPI at https://aka.ms/aspnetcore/swashbuckle
//builder.Services.AddDbContext<TodoContext>(opt =>
//  opt.UseInMemoryDatabase("TodoList"));

builder.Services.Configure<AppSettings>(builder.Configuration.GetSection("AppSettings"));

builder.Services.AddDbContext<Interno.Outset.Models.Temp.TulipContext>(
    dbContextOptions => dbContextOptions
        .UseMySql(builder.Configuration.GetSection("AppSettings")["DatalogTulip"]?.ToString(), new MySqlServerVersion(new Version(8, 0, 33)))
        // The following three options help with debugging, but should
        // be changed or removed for production.
        .LogTo(Console.WriteLine, LogLevel.Information)
        .EnableSensitiveDataLogging()
        .EnableDetailedErrors()
);

builder.Services.AddDbContext<Interno.Outset.Models.OutsetContext>(
    dbContextOptions => dbContextOptions
        .UseMySql(builder.Configuration.GetSection("AppSettings")["Database"]?.ToString(), new MySqlServerVersion(new Version(8, 0, 33)))
        // The following three options help with debugging, but should
        // be changed or removed for production.
        .LogTo(Console.WriteLine, LogLevel.Information)
        .EnableSensitiveDataLogging()
        .EnableDetailedErrors()
);

builder.Services.AddDbContext<Interno.Production.Models.ProductionContext>(
    dbContextOptions => dbContextOptions
        .UseMySql(builder.Configuration.GetSection("AppSettings")["Database"]?.ToString(), new MySqlServerVersion(new Version(8, 0, 33)))
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

app.UseCors(MyAllowSpecificOrigins);
app.UseHttpsRedirection();
app.UseAuthorization();
app.MapControllers();

// using (var scope = app.Services.CreateScope())
// {
//     //Resolve dbcontext with DI help
//     var dbcontext = (OutsetContext)scope.ServiceProvider.GetService(typeof(OutsetContext));

//     //call your static method herer

// //     Interno.Outset.DbInitilizer.Initializer(dbcontext);;
// // }
// string ipAddress = "10.7.51.217";
// string zpl = "^XA^FO100,100^FDPrueba de impresión con Python^FS^XZ";

// System.Net.Sockets.TcpClient client = new System.Net.Sockets.TcpClient();
// client.Connect(ipAddress, 9100);

// // Write ZPL String to connection
// System.IO.StreamWriter writer = new System.IO.StreamWriter(client.GetStream());
// writer.Write(zpl);
// writer.Flush();

// // Close Connection
// writer.Close();
// client.Close();
app.Run();