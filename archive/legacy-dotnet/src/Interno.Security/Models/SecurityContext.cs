using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Interno.Security.Models;
using Interno.Domain.Catalog;

namespace Interno.Security.Models
{
    public class SecurityContext : DbContext
    {
        public SecurityContext(DbContextOptions<SecurityContext> options) : base(options) { }

        public DbSet<Interno.Security.Models.SecurityGuard> SecurityGuard { get; set; }
        public DbSet<Interno.Security.Models.EmployeeLog> EmployeeLog { get; set; }

        public DbSet<Interno.Security.Models.VisitLog> VisitLog { get; set; }
        public DbSet<Interno.Domain.Catalog.Person> Persons { get; set; }
    }
}