using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Hosting;
using Microsoft.Extensions.Configuration;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Hosting;
using Microsoft.Extensions.Logging;

using Microsoft.AspNetCore.Http.Features;
using Microsoft.EntityFrameworkCore;

using Interno.DJO.Helpers;

namespace Interno.DJO
{
    public class Startup
    {
        public Startup(IConfiguration configuration)
        {
            Configuration = configuration;
        }
        public IConfiguration Configuration { get; }

        // This method gets called by the runtime. Use this method to add services to the container.
        public void ConfigureServices(IServiceCollection services)
        {
            System.Text.Encoding.RegisterProvider(System.Text.CodePagesEncodingProvider.Instance);
            services.AddCors();
            //Ser Settings
            services.Configure<AppSettings>(Configuration.GetSection("AppSettings"));
            //Email Service
            services.AddScoped<Interno.DJO.Services.IEmailService, Interno.DJO.Services.EmailService>();

            //Context
            services.AddDbContextPool<DJOContext>(options => options
                .UseMySql(Configuration.GetSection("AppSettings")["Database"].ToString(), x => x.ServerVersion("8.0.13-mysql"))
                .UseLoggerFactory(LoggerFactory.Create(b => b.AddConsole().AddFilter(level => level >= LogLevel.Information)))
                .EnableSensitiveDataLogging()
                .EnableDetailedErrors()
            );
            services.AddDbContextPool<Interno.Production.Models.ProductionContext>(options => options
                .UseMySql(Configuration.GetSection("AppSettings")["Database"].ToString(), x => x.ServerVersion("8.0.13-mysql"))
                .UseLoggerFactory(LoggerFactory.Create(b => b.AddConsole().AddFilter(level => level >= LogLevel.Information)))
                .EnableSensitiveDataLogging()
                .EnableDetailedErrors()
            );
            services.AddDbContextPool<Interno.HumanResource.Models.HRContext>(options => options
                .UseMySql(Configuration.GetSection("AppSettings")["Database"].ToString(), x => x.ServerVersion("8.0.30-mysql"))
                .UseLoggerFactory(LoggerFactory.Create(b => b
                    .AddConsole()
                    .AddFilter(level => level >= LogLevel.Information)))
                .EnableSensitiveDataLogging()
                .EnableDetailedErrors()
            );
            //Json Recursivity
            services.AddControllers()
                .AddNewtonsoftJson(opt => opt.SerializerSettings.ReferenceLoopHandling = Newtonsoft.Json.ReferenceLoopHandling.Ignore);

            //Memory Limit to Upload Files
            services.Configure<FormOptions>(o =>
            {
                o.ValueLengthLimit = int.MaxValue;
                o.MultipartBodyLengthLimit = long.MaxValue;
                o.MemoryBufferThreshold = int.MaxValue;
            });
        }

        // This method gets called by the runtime. Use this method to configure the HTTP request pipeline.
        public void Configure(IApplicationBuilder app, IWebHostEnvironment env, DJOContext context)
        {
            if (env.IsDevelopment())
            {
                app.UseDeveloperExceptionPage();
            }
            app.UseHttpsRedirection();

            app.UseCors(x => x
                .AllowAnyMethod()
                .AllowAnyHeader()
                .SetIsOriginAllowed(origin => true) // allow any origin
                .AllowCredentials()); // allow credentials
            // app.UseCors(x => x
            //     .WithOrigins("http://10.60.10.176")
            //     .AllowAnyMethod()
            //     .AllowAnyHeader());
            //     //.AllowCredentials());

            app.UsePathBase(new Microsoft.AspNetCore.Http.PathString("/api/enovis/"));
            app.UseRouting();
            app.UseAuthorization();
            app.UseAuthentication();
            app.UseEndpoints(endpoints =>
            {
                endpoints.MapControllers();
            });
            //Interno.DJO.Data.DbInitilizer.Initializer(context);
        }
    }
}
