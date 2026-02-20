using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;
using System.ComponentModel.DataAnnotations;
using System.ComponentModel.DataAnnotations.Schema;
using Interno.Domain.Catalog;

namespace Interno.Security.Models
{
    public class SecurityGuard
    {
        [Key]
        public int Id { get; set; }
        [Required]
        public int PersonId { get; set; }
        
        public Person Person { get; set; }

    }
}