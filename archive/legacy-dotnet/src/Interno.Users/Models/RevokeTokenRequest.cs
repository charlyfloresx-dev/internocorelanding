using System;
using System.Collections.Generic;
using System.Linq;
using System.Threading.Tasks;

using System.ComponentModel.DataAnnotations;

namespace Interno.Users.Models
{
    public class RevokeTokenRequest
    {
        public string Token { get; set; }
    }
}