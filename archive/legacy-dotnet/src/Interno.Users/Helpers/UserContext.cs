using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.EntityFrameworkCore;
using Interno.Users.Entities;

namespace Interno.Users.Helpers
{
    public class UserContext : DbContext
    {
        public DbSet<Interno.Users.Entities.User> User { get; set; }
        public UserContext(DbContextOptions<UserContext> options) : base(options) { }
    }
}